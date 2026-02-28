from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Board, Post, Like
from app.schemas import BoardCreate, PostCreate, ReplyCreate


# ── Board ────────────────────────────────────────────

def get_boards(db: Session, active_only: bool = True) -> list[dict]:
    query = db.query(Board)
    if active_only:
        query = query.filter(Board.is_active == True)
    boards = query.order_by(Board.sort_order, Board.id).all()

    result = []
    for b in boards:
        count = (
            db.query(func.count(Post.id))
            .filter(Post.board_id == b.id, Post.parent_id == None, Post.is_deleted == False)
            .scalar()
        )
        latest = (
            db.query(Post)
            .filter(Post.board_id == b.id, Post.parent_id == None, Post.is_deleted == False)
            .order_by(desc(Post.created_at))
            .first()
        )
        result.append({
            "board": b,
            "post_count": count,
            "latest_post": latest,
        })
    return result


def get_board_by_slug(db: Session, slug: str) -> Board | None:
    return db.query(Board).filter(Board.slug == slug).first()


def create_board(db: Session, data: BoardCreate) -> Board:
    board = Board(**data.model_dump())
    db.add(board)
    db.commit()
    db.refresh(board)
    return board


# ── Post ─────────────────────────────────────────────

def _get_like_info(db: Session, post_id: int) -> dict:
    count = db.query(func.count(Like.id)).filter(Like.post_id == post_id).scalar()
    authors = [r[0] for r in db.query(Like.author).filter(Like.post_id == post_id).order_by(Like.created_at).all()]
    return {"like_count": count, "liked_by": authors}


def get_posts(db: Session, board_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    posts = (
        db.query(Post)
        .filter(Post.board_id == board_id, Post.parent_id == None, Post.is_deleted == False)
        .order_by(desc(Post.is_pinned), desc(Post.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )
    result = []
    for p in posts:
        reply_count = (
            db.query(func.count(Post.id))
            .filter(Post.parent_id == p.id, Post.is_deleted == False)
            .scalar()
        )
        like_info = _get_like_info(db, p.id)
        result.append({"post": p, "reply_count": reply_count, **like_info})
    return result


def get_post(db: Session, post_id: int) -> dict | None:
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        return None
    replies = (
        db.query(Post)
        .filter(Post.parent_id == post_id, Post.is_deleted == False)
        .order_by(Post.created_at)
        .all()
    )
    board = db.query(Board).filter(Board.id == post.board_id).first()
    like_info = _get_like_info(db, post.id)
    # 댓글별 좋아요 정보도 포함
    replies_with_likes = []
    for r in replies:
        r_like = _get_like_info(db, r.id)
        replies_with_likes.append({"reply": r, **r_like})
    return {"post": post, "replies": replies_with_likes, "board": board, **like_info}


def create_post(db: Session, data: PostCreate) -> Post:
    board = get_board_by_slug(db, data.board_slug)
    if not board:
        raise ValueError(f"Board '{data.board_slug}' not found")
    post = Post(
        board_id=board.id,
        title=data.title,
        content=data.content,
        author=data.author,
        prefix=data.prefix,
        tag=data.tag,
        is_pinned=data.is_pinned,
    )
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def create_reply(db: Session, post_id: int, data: ReplyCreate) -> Post:
    parent = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not parent:
        raise ValueError(f"Post {post_id} not found")
    reply = Post(
        board_id=parent.board_id,
        parent_id=post_id,
        content=data.content,
        author=data.author,
    )
    db.add(reply)
    db.commit()
    db.refresh(reply)
    return reply


def update_post(db: Session, post_id: int, title: str | None = None, content: str | None = None) -> Post | None:
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        return None
    if title is not None:
        post.title = title
    if content is not None:
        post.content = content
    db.commit()
    db.refresh(post)
    return post


def delete_post(db: Session, post_id: int) -> bool:
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        return False
    post.is_deleted = True
    # soft-delete replies too
    db.query(Post).filter(Post.parent_id == post_id).update({"is_deleted": True})
    db.commit()
    return True


def restore_post(db: Session, post_id: int) -> bool:
    """소프트 삭제된 글을 복구한다."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == True).first()
    if not post:
        return False
    post.is_deleted = False
    # replies도 함께 복구
    db.query(Post).filter(Post.parent_id == post_id, Post.is_deleted == True).update({"is_deleted": False})
    db.commit()
    return True


def search_posts(db: Session, keyword: str, board_slug: str | None = None, limit: int = 20) -> list[dict]:
    query = db.query(Post).filter(
        Post.parent_id == None,
        Post.is_deleted == False,
        (Post.title.contains(keyword) | Post.content.contains(keyword)),
    )
    if board_slug:
        board = db.query(Board).filter(Board.slug == board_slug).first()
        if board:
            query = query.filter(Post.board_id == board.id)
    posts = query.order_by(desc(Post.created_at)).limit(limit).all()
    result = []
    for p in posts:
        board = db.query(Board).filter(Board.id == p.board_id).first()
        reply_count = db.query(func.count(Post.id)).filter(Post.parent_id == p.id, Post.is_deleted == False).scalar()
        like_info = _get_like_info(db, p.id)
        result.append({"post": p, "reply_count": reply_count, "board": board, **like_info})
    return result


def get_recent_posts(db: Session, limit: int = 10) -> list[dict]:
    posts = (
        db.query(Post)
        .filter(Post.parent_id == None, Post.is_deleted == False)
        .order_by(desc(Post.created_at))
        .limit(limit)
        .all()
    )
    result = []
    for p in posts:
        board = db.query(Board).filter(Board.id == p.board_id).first()
        reply_count = db.query(func.count(Post.id)).filter(Post.parent_id == p.id, Post.is_deleted == False).scalar()
        like_info = _get_like_info(db, p.id)
        result.append({"post": p, "reply_count": reply_count, "board": board, **like_info})
    return result


def get_post_count(db: Session, board_id: int) -> int:
    return (
        db.query(func.count(Post.id))
        .filter(Post.board_id == board_id, Post.parent_id == None, Post.is_deleted == False)
        .scalar()
    )


# ── Like ──────────────────────────────────────────

def toggle_like(db: Session, post_id: int, author: str) -> dict:
    """좋아요 토글. 이미 있으면 취소, 없으면 추가."""
    post = db.query(Post).filter(Post.id == post_id, Post.is_deleted == False).first()
    if not post:
        raise ValueError(f"Post {post_id} not found")
    existing = db.query(Like).filter(Like.post_id == post_id, Like.author == author).first()
    if existing:
        db.delete(existing)
        db.commit()
        action = "unliked"
    else:
        like = Like(post_id=post_id, author=author)
        db.add(like)
        db.commit()
        action = "liked"
    return {"action": action, **_get_like_info(db, post_id)}


def get_likes(db: Session, post_id: int) -> dict:
    return _get_like_info(db, post_id)
