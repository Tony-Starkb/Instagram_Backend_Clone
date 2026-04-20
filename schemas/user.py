from pydantic import AnyHttpUrl, BaseModel, EmailStr
from enum import Enum


class Role(str, Enum):
    USER = "user"
    MODERATOR = "moderator" 
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"
    

class UserCreate(BaseModel):
    
    email: EmailStr
    username: str
    password: str
    full_name: str
    bio: str
    role: Role
    

class UserResponse(BaseModel):
    
    id: int
    username: str
    bio: str | None = None
    avatar_url: AnyHttpUrl
    follower_count: int
    following_count: int
    post_count: int

	