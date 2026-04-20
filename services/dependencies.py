import os
from dotenv import load_dotenv
from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.exceptions import HTTPException
from typing import Annotated
import jwt
from pydantic import BaseModel
from datetime import datetime, timezone, timedelta
import bcrypt
from services import db_handler



load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINS = os.getenv("ACCESS_TOKEN_EXPIRE_MINS")
REFRESH_TOKEN_EXPIRE_DAYS = os.getenv("REFRESH_TOKEN_EXPIRE_DAYS")


class TokenData(BaseModel):
    username: str | None = None



oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def password_to_hash(userpassword: str):
	salt = bcrypt.gensalt(rounds=12)
	return bcrypt.hashpw(userpassword.encode('utf-8'), salt).decode('utf-8')


def validate_password_hash(userpassword: str, passwordhash: str):
	return bcrypt.checkpw(
		userpassword.encode('utf-8'),
		passwordhash.encode('utf-8')
	)
 
 
def authenticate_user(username: str, password: str):
    user = db_handler.get_user_by_username(username)
     
    if user is None:
         raise HTTPException (
            status_code = 401,
            detail = "Invalid username or password"
		 )
    
    if not validate_password_hash(password, user['password_hash']):
        raise HTTPException (
			status_code = 401,
            detail = "Invalid username or password"
		)
    
    return user


# get_current_user: function to return the details about the user that is trying to login the application
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):

	credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("username")
		if username is None:
			raise credentials_exception
		token_data = TokenData(username=username)

	except jwt.InvalidTokenError:
		raise credentials_exception

	return token_data


# function to create a jwt token based on the payloadwe pass to it
def create_token(payload: dict, expire_time: timedelta | None=None):
	to_encode = payload.copy()

	if expire_time:
		expire = datetime.now(timezone.utc) + expire_time
	else:
		expire = datetime.now(timezone.utc) + timedelta(minutes=15)

	to_encode.update({"exp": expire})

	jwt_token = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return jwt_token

