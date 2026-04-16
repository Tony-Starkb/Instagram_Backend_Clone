from pydantic import BaseModel, EmailStr, AnyHttpUrl
from schemas.user import UserResponse



class PostCreate(BaseModel):
    
    caption: str
    image_url: AnyHttpUrl
    
    
    
class PostResponse(BaseModel):
    
    id: int
    caption: str
    author: UserResponse
    like_count: int
    comment_count: int
    created_at: str