from pydantic import BaseModel
from datetime import datetime


class BoardCreate(BaseModel):
    name: str
    slug: str
    category: str = "global"
    team: str | None = None
    description: str = ""
    icon: str = ""
    sort_order: int = 0


class BoardOut(BaseModel):
    id: int
    name: str
    slug: str
    category: str
    team: str | None
    description: str
    icon: str
    sort_order: int
    is_active: bool
    created_at: datetime
    post_count: int = 0

    class Config:
        from_attributes = True


class PostCreate(BaseModel):
    board_slug: str
    title: str
    content: str
    author: str
    prefix: str | None = None
    is_pinned: bool = False


class PostUpdate(BaseModel):
    title: str | None = None
    content: str | None = None


class ReplyCreate(BaseModel):
    content: str
    author: str


class LikeCreate(BaseModel):
    author: str


class PostOut(BaseModel):
    id: int
    board_id: int
    parent_id: int | None
    title: str | None
    content: str
    author: str
    prefix: str | None
    is_pinned: bool
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
    reply_count: int = 0
    like_count: int = 0
    liked_by: list[str] = []
    board_slug: str = ""
    board_name: str = ""

    class Config:
        from_attributes = True
