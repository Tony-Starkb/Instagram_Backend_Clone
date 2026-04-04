from pydantic import BaseModel, EmailStr, HttpUrl



class Posts(BaseModel):
	capthon: str
	image_url: HttpUrl