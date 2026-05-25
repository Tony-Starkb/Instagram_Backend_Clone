from pydantic import AnyHttpUrl, BaseModel, ConfigDict, Field
from uuid import UUID


class PostCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str = Field(min_length=1, max_length=2200)
    image_url: AnyHttpUrl


class PostUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    caption: str | None = Field(default=None, min_length=1, max_length=2200)
    image_url: AnyHttpUrl | None = None


class PostResponse(BaseModel):
    id: UUID
    username: str
    caption: str
    image_url: AnyHttpUrl
    like_count: int
    comment_count: int
    created_at: str
    updated_at: str | None = None
