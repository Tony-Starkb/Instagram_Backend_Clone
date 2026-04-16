"""
Here in this module we will do all the authentication related work like login, logout, token generation 
and validation, password hashing and verification etc.

"""
 

from fastapi import APIRouter, status, Request
from fastapi.responses import JSONResponse
from services import db_handler
from schemas.user import UserCreate, UserResponse
from core.exceptions import UserNotFound, PostNotFound
from services.user_input_validation import validate_password, validate_username
from fastapi.exceptions import HTTPException
import bcrypt
import uuid
from datetime import datetime, timezone


auth_router = APIRouter(prefix = "/api/v1/auth", tags = ["auth"])



def password_to_hash(userpassword: str):
	salt = bcrypt.gensalt(rounds=12)
	return bcrypt.hashpw(userpassword.encode('utf-8'), salt).decode('utf-8')


def validate_password_hash(userpassword: str, passwordhash: str):
	return bcrypt.chech(
		userpassword.encode('utf-8'),
		passwordhash.encode('utf-8')
	)



# first here taking the input from the users (either username/password or email/passwors)
@auth_router.post("/login")
def user_login(username: str, password: str):
	if validate_username(username):
		raise HTTPException (
			status_code = 422,
			detail = "Unprocessable Entity"
		)

	if validate_password(password):
		raise HTTPException (
			status_code = 422,
			detail = "Unprocessable Entity"
		)

	user = db_handler.get_user_by_username(username)

	if not user:
		raise HTTPException(
			status_code = 401,
			detail = "Something went wrong"
		)
	
	if not validate_password_hash(password, user["password_hash"]):
		raise HTTPException(
			status_code = 401,
			detail = "Something went wrong"
		)
	

	return JSONResponse ({
		"message": "user validated",
		"user": user
	})


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