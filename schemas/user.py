from enum import Enum

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field


class Role(str, Enum):
    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"
    SUPER_ADMIN = "super_admin"


class UserCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    username: str
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=1, max_length=100)
    bio: str = Field(default="", max_length=150)
    avatar_url: AnyHttpUrl | None = None


class UserPublicResponse(BaseModel):
    id: str
    username: str
    full_name: str
    bio: str | None = None
    avatar_url: AnyHttpUrl
    is_private: bool
    is_verified: bool
    follower_count: int
    following_count: int
    post_count: int
    created_at: str
