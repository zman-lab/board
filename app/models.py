from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, backref
from app.database import Base


def _utcnow():
    return datetime.now(timezone.utc)


class Board(Base):
    __tablename__ = "boards"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    category = Column(String(20), nullable=False)  # "team" | "global"
    team = Column(String(50), nullable=True)
    description = Column(Text, default="")
    icon = Column(String(10), default="")
    sort_order = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utcnow)

    posts = relationship("Post", back_populates="board")


class Post(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False, index=True)
    parent_id = Column(Integer, ForeignKey("posts.id"), nullable=True, index=True)
    title = Column(String(200), nullable=True)
    content = Column(Text, nullable=False)
    author = Column(String(100), nullable=False)
    prefix = Column(String(50), nullable=True)
    is_pinned = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    board = relationship("Board", back_populates="posts")
    replies = relationship(
        "Post",
        backref=backref("parent", remote_side="Post.id"),
        foreign_keys=[parent_id],
        lazy="select",
    )
    likes = relationship("Like", back_populates="post", cascade="all, delete-orphan")


class Like(Base):
    __tablename__ = "likes"
    __table_args__ = (
        UniqueConstraint("post_id", "author", name="uq_like_post_author"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, index=True)
    author = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=_utcnow)

    post = relationship("Post", back_populates="likes")
