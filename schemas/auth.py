from pydantic import BaseModel, EmailStr, AnyHttpUrl


class LoginRequest(BaseModel):
    
    email: EmailStr
    password: str
    
    
class TakenResponse(BaseModel):
    
    assess_tokef: str
    refresh_token: str
    refresh_token: str = "bearer"
    
    