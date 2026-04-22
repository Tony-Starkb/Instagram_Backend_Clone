from datetime import datetime, timedelta, timezone
import os
import uuid
from typing import Annotated, Optional

from dotenv import load_dotenv
import jwt
from fastapi import APIRouter, Depends, Response, status, Cookie
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from services import db_handler
from schemas.user import UserCreate
from schemas.auth import TokenResponse
from services.user_input_validation import validate_password, validate_username
from services.dependencies import authenticate_user, create_token, password_to_hash


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINS = os.getenv("ACCESS_TOKEN_EXPIRE_MINS")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"


auth_router = APIRouter(prefix = "/api/v1/auth", tags = ["auth"])


# first here taking the input from the users (either username/password or email/passwors)
@auth_router.post("/login")
def user_login(
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> TokenResponse:
    authenticated_user = authenticate_user(user.username, user.password)
    print("USER FROM DB:", authenticated_user['id'], authenticated_user['username'])
        
    access_token_expire = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINS))
    accessToken = create_token (
		payload={"username": authenticated_user['username'], "role": authenticated_user['role']},
		expire_time=access_token_expire
	)
    
    refresh_token_expire = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    refresh_token = create_token(
		payload={"username": authenticated_user['username'], "role": authenticated_user['role'], "type": "refresh"},
        expire_time=refresh_token_expire
	)
    
    response.set_cookie(
		key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
	)
    
    refresh_token_data = {
    	"id": str(uuid.uuid4()),
    	"user_id": authenticated_user['id'],  
    	"token": refresh_token,
    	"is_revoked": False,                
    	"created_at": datetime.now(timezone.utc).isoformat(),
    	"expires_at": (datetime.now(timezone.utc) + refresh_token_expire).isoformat(),
	}
    
    db_handler.save_refresh_token(refresh_token_data)
    
    return TokenResponse (access_token = accessToken, token_type = "bearer")


@auth_router.post("/refresh")
def renue_refresh_token(
    response: Response,
	refresh_token: Optional[str] = Cookie(None),
) -> TokenResponse:
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    ## raise the error 401 if no cookie of refresh token is found
    if refresh_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="token not found in cookies",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    print("TOKEN FROM COOKIE:", refresh_token)
    token_in_db = db_handler.get_refresh_token(refresh_token)
    print("TOKEN IN DB:", token_in_db)
    
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="invalid refresh token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except jwt.InvalidTokenError:
        raise credentials_exception
    
    
    token_in_db = db_handler.get_refresh_token(refresh_token)
    if not token_in_db:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token not found in DB",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if token_in_db.get("is_revoked") == True:
        db_handler.delete_all_user_tokens(token_in_db["user_id"])
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    expires_at = datetime.fromisoformat(token_in_db.get("expires_at"))
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="refresh token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    db_handler.revoke_refresh_token(refresh_token)
    
    user = db_handler.get_user_by_id(token_in_db["user_id"])
    
    access_token_expire = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINS))
    accessToken = create_token (
		payload={"username": user['username'], "role": user['role']},
		expire_time=access_token_expire
	)
    
    refresh_token_expire = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    refresh_token = create_token(
		payload={"username": user['username'], "role": user['role'], "type": "refresh"},
        expire_time=refresh_token_expire
	)
    
    response.set_cookie(
		key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=COOKIE_SECURE,
        samesite="lax",
        max_age=int(REFRESH_TOKEN_EXPIRE_DAYS) * 24 * 60 * 60
	)
    
    refresh_token_data = {
    	"id": str(uuid.uuid4()),
    	"user_id": token_in_db["user_id"],  
    	"token": refresh_token,
    	"is_revoked": False,                
    	"created_at": datetime.now(timezone.utc).isoformat(),
    	"expires_at": (datetime.now(timezone.utc) + refresh_token_expire).isoformat(),
	}
    
    db_handler.save_refresh_token(refresh_token_data)
    
    return TokenResponse (access_token = accessToken, token_type = "bearer")
    
    


@auth_router.post("/registration")
def user_registration(user: UserCreate):
	user_username = db_handler.get_user_by_username(user.username)
	user_email = db_handler.get_user_by_email(user.email)

	if user_username:
		raise HTTPException (
			status_code = 409,
			detail = "Username already exists."
		)

	if user_email:
		raise HTTPException (
			status_code = 409,
			detail = "Email already exists."
		)

	validate_username(user.username)
	validate_password(user.password)

	hashed_password = password_to_hash(user.password)
	now_utc = datetime.now(timezone.utc)

	new_user = {
		"id": str(uuid.uuid4()),
		"email": user.email,
		"username": user.username,
		"password_hash": hashed_password,
		"full_name": user.full_name,
		"bio": user.bio,
		"avatar_url": str(user.avatar_url) if user.avatar_url else None,
		"is_private": False,
		"is_verified": False,
		"role": "user",
		"followers": [],
		"following": [],
		"created_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
	}

	created_user = db_handler.add_user(new_user)

	return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content={
		    "message": "Account created successfully.",
		    "user": {
                "id": created_user["id"],
                "username": created_user["username"],
                "email": created_user["email"],
            },
	    },
    )
 
