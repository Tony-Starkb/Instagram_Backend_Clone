from pydantic import AnyHttpUrl, BaseModel, EmailStr



class UserCreate(BaseModel):
    
    email: EmailStr
    username: str
    password: str
    full_name: str
    bio: str
    

class UserResponse(BaseModel):
    
    id: int
    username: str
    bio: str | None = None
    avatar_url: AnyHttpUrl
    follower_count: int
    following_count: int
    post_count: int

	