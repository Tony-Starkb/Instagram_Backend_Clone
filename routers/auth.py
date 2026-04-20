"""
Here in this module we will do all the authentication related work like login, logout, token generation 
and validation, password hashing and verification etc.

"""
 

from fastapi import APIRouter, Depends, Response
from fastapi.responses import JSONResponse
from services import db_handler
from schemas.user import UserCreate
from schemas.auth import TokenResponse
from services.user_input_validation import validate_password, validate_username
from fastapi.exceptions import HTTPException
import uuid
from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi.security import OAuth2PasswordRequestForm
import os
from dotenv import load_dotenv
from services.dependencies import create_token, validate_password_hash, authenticate_user, password_to_hash


load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINS = os.getenv("ACCESS_TOKEN_EXPIRE_MINS")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")


auth_router = APIRouter(prefix = "/api/v1/auth", tags = ["auth"])


# first here taking the input from the users (either username/password or email/passwors)
@auth_router.post("/login")
def user_login(
    user: Annotated[OAuth2PasswordRequestForm, Depends()],
    response: Response,
) -> TokenResponse:
    user = authenticate_user(user.username, user.password)
        
    access_token_expire = timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINS))
    accessToken = create_token (
		payload={"username": user['username'], "role": user['role']},
		expire_time=access_token_expire
	)
    
    refresh_token_expire = timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS))
    refresh_token = create_token(
		payload={"username":user['username'], "role": user['role']},
        expire_time=refresh_token_expire
	)
    
    response.set_cookie(
		key='refresh_token',
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",       
        max_age=7 * 24 * 60 * 60
	)
    
    return TokenResponse (access_token = accessToken, token_type = "bearer")



@auth_router.post("/registration")
def user_registration(user: UserCreate):

	user_username = db_handler.get_user_by_username(user.username);
	user_email = db_handler.get_user_by_email(user.email)

	if(user_username):
		raise HTTPException (
			status_code = 409,
			detail = "username already exist"
		)

	if(user_email):
		raise HTTPException (
			status_code = 409,
			detail = "email already exist"
		)

	if validate_username(user.username):
		raise HTTPException (
			status_code = 422,
			detail = "Unprocessable Entity"
		)

	if validate_password(user.password):
		raise HTTPException (
			status_code = 422,
			detail = "Unprocessable Entity"
		)

	hashed_password = password_to_hash(user.password)
	now_utc = datetime.now(timezone.utc)

	new_user = {
		"id": str(uuid.uuid4()),
		"email": user.email,
		"username": user.username,
		"password_hash": hashed_password,
		"full_name": user.full_name,
		"bio": user.bio,
		"created_at": now_utc.strftime("%Y-%m-%dT%H:%M:%SZ")
	}

	db_handler.add_user(new_user)

	return JSONResponse ({
		"message": "Account created successfully",
		"User Details": f"UserName: {user.username}, EMail: {user.email}"	
	})
 
