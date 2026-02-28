from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Depends, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.seed import seed_data
from app import crud
from app.schemas import BoardCreate, PostCreate, PostUpdate, ReplyCreate, LikeCreate


@asynccontextmanager
async def lifespan(_app: FastAPI):
    init_db()
    db = next(get_db())
    try:
        seed_data(db)
    finally:
        db.close()
    yield


app = FastAPI(title="Claude Board", lifespan=lifespan)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")


def _time_ago(dt: datetime) -> str:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    diff = datetime.now(timezone.utc) - dt
    seconds = int(diff.total_seconds())
    if seconds < 60:
        return "방금 전"
    if seconds < 3600:
        return f"{seconds // 60}분 전"
    if seconds < 86400:
        return f"{seconds // 3600}시간 전"
    if seconds < 604800:
        return f"{seconds // 86400}일 전"
    return dt.strftime("%Y-%m-%d")


templates.env.filters["time_ago"] = _time_ago


# ── HTML Pages ───────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
def index(request: Request, db: Session = Depends(get_db)):
    boards = crud.get_boards(db)
    return templates.TemplateResponse("index.html", {"request": request, "boards": boards})


@app.get("/board/{slug}", response_class=HTMLResponse)
def board_page(slug: str, request: Request, page: int = 1, db: Session = Depends(get_db)):
    board = crud.get_board_by_slug(db, slug)
    if not board:
        raise HTTPException(404, "게시판을 찾을 수 없습니다")
    limit = 20
    offset = (page - 1) * limit
    posts = crud.get_posts(db, board.id, limit=limit, offset=offset)
    total = crud.get_post_count(db, board.id)
    total_pages = max(1, (total + limit - 1) // limit)
    return templates.TemplateResponse("board.html", {
        "request": request, "board": board, "posts": posts,
        "page": page, "total_pages": total_pages, "total": total,
    })


@app.get("/post/{post_id}", response_class=HTMLResponse)
def post_page(post_id: int, request: Request, db: Session = Depends(get_db)):
    data = crud.get_post(db, post_id)
    if not data:
        raise HTTPException(404, "게시글을 찾을 수 없습니다")
    return templates.TemplateResponse("post.html", {"request": request, **data})


# ── Like Form Action ────────────────────────────────

@app.post("/action/like/{post_id}")
def action_toggle_like(
    post_id: int,
    author: str = Form(...),
    redirect_to: str = Form(""),
    db: Session = Depends(get_db),
):
    try:
        crud.toggle_like(db, post_id, author)
    except ValueError:
        raise HTTPException(404, "게시글을 찾을 수 없습니다")
    target = redirect_to or f"/post/{post_id}"
    return RedirectResponse(target, status_code=303)


@app.get("/new/{slug}", response_class=HTMLResponse)
def new_post_page(slug: str, request: Request, db: Session = Depends(get_db)):
    board = crud.get_board_by_slug(db, slug)
    if not board:
        raise HTTPException(404, "게시판을 찾을 수 없습니다")
    return templates.TemplateResponse("new_post.html", {"request": request, "board": board})


# ── Form Actions ─────────────────────────────────────

@app.post("/action/post")
def action_create_post(
    board_slug: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    author: str = Form(...),
    prefix: str = Form(""),
    tag: str = Form(""),
    db: Session = Depends(get_db),
):
    data = PostCreate(
        board_slug=board_slug, title=title, content=content,
        author=author, prefix=prefix or None, tag=tag or None,
    )
    post = crud.create_post(db, data)
    return RedirectResponse(f"/post/{post.id}", status_code=303)


@app.post("/action/reply/{post_id}")
def action_create_reply(
    post_id: int,
    content: str = Form(...),
    author: str = Form(...),
    db: Session = Depends(get_db),
):
    data = ReplyCreate(content=content, author=author)
    crud.create_reply(db, post_id, data)
    return RedirectResponse(f"/post/{post_id}", status_code=303)


# ── REST API ─────────────────────────────────────────

@app.get("/api/boards")
def api_list_boards(db: Session = Depends(get_db)):
    boards = crud.get_boards(db)
    return [
        {
            "id": b["board"].id, "name": b["board"].name, "slug": b["board"].slug,
            "category": b["board"].category, "team": b["board"].team,
            "icon": b["board"].icon, "description": b["board"].description,
            "post_count": b["post_count"],
        }
        for b in boards
    ]


@app.get("/api/posts")
def api_list_posts(board_slug: str | None = None, limit: int = 20, offset: int = 0, db: Session = Depends(get_db)):
    if board_slug:
        board = crud.get_board_by_slug(db, board_slug)
        if not board:
            raise HTTPException(404, "Board not found")
        posts = crud.get_posts(db, board.id, limit=limit, offset=offset)
    else:
        posts = crud.get_recent_posts(db, limit=limit)
    return [
        {
            "id": p["post"].id, "title": p["post"].title, "author": p["post"].author,
            "prefix": p["post"].prefix, "tag": p["post"].tag, "is_pinned": p["post"].is_pinned,
            "created_at": p["post"].created_at.isoformat(),
            "updated_at": p["post"].updated_at.isoformat() if p["post"].updated_at else None,
            "reply_count": p["reply_count"],
            "like_count": p["like_count"], "liked_by": p["liked_by"],
        }
        for p in posts
    ]


@app.get("/api/posts/{post_id}")
def api_get_post(post_id: int, db: Session = Depends(get_db)):
    data = crud.get_post(db, post_id)
    if not data:
        raise HTTPException(404, "Post not found")
    return {
        "id": data["post"].id, "title": data["post"].title,
        "content": data["post"].content, "author": data["post"].author,
        "prefix": data["post"].prefix, "tag": data["post"].tag, "is_pinned": data["post"].is_pinned,
        "created_at": data["post"].created_at.isoformat(),
        "updated_at": data["post"].updated_at.isoformat() if data["post"].updated_at else None,
        "board_slug": data["board"].slug, "board_name": data["board"].name,
        "like_count": data["like_count"], "liked_by": data["liked_by"],
        "replies": [
            {
                "id": r["reply"].id, "content": r["reply"].content, "author": r["reply"].author,
                "created_at": r["reply"].created_at.isoformat(),
                "updated_at": r["reply"].updated_at.isoformat() if r["reply"].updated_at else None,
                "like_count": r["like_count"], "liked_by": r["liked_by"],
            }
            for r in data["replies"]
        ],
    }


@app.post("/api/posts")
def api_create_post(data: PostCreate, db: Session = Depends(get_db)):
    try:
        post = crud.create_post(db, data)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return {"id": post.id, "title": post.title, "created_at": post.created_at.isoformat()}


@app.post("/api/posts/{post_id}/reply")
def api_create_reply(post_id: int, data: ReplyCreate, db: Session = Depends(get_db)):
    try:
        reply = crud.create_reply(db, post_id, data)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return {"id": reply.id, "created_at": reply.created_at.isoformat()}


@app.post("/api/posts/{post_id}/like")
def api_toggle_like(post_id: int, data: LikeCreate, db: Session = Depends(get_db)):
    try:
        result = crud.toggle_like(db, post_id, data.author)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return result


@app.get("/api/posts/{post_id}/likes")
def api_get_likes(post_id: int, db: Session = Depends(get_db)):
    return crud.get_likes(db, post_id)


@app.put("/api/posts/{post_id}")
def api_update_post(post_id: int, data: PostUpdate, db: Session = Depends(get_db)):
    post = crud.update_post(db, post_id, title=data.title, content=data.content)
    if not post:
        raise HTTPException(404, "Post not found")
    return {
        "id": post.id, "title": post.title, "content": post.content,
        "updated_at": post.updated_at.isoformat() if post.updated_at else None,
    }


@app.delete("/api/posts/{post_id}")
def api_delete_post(post_id: int, db: Session = Depends(get_db)):
    ok = crud.delete_post(db, post_id)
    if not ok:
        raise HTTPException(404, "Post not found")
    return {"ok": True}


@app.post("/api/posts/{post_id}/restore")
def api_restore_post(post_id: int, db: Session = Depends(get_db)):
    ok = crud.restore_post(db, post_id)
    if not ok:
        raise HTTPException(404, "Post not found or not deleted")
    return {"ok": True, "post_id": post_id}


@app.post("/api/boards")
def api_create_board(data: BoardCreate, db: Session = Depends(get_db)):
    existing = crud.get_board_by_slug(db, data.slug)
    if existing:
        raise HTTPException(409, f"Board '{data.slug}' already exists")
    board = crud.create_board(db, data)
    return {"id": board.id, "slug": board.slug}


@app.get("/api/search")
def api_search(q: str, board_slug: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    results = crud.search_posts(db, q, board_slug=board_slug, limit=limit)
    return [
        {
            "id": r["post"].id, "title": r["post"].title, "author": r["post"].author,
            "board_slug": r["board"].slug if r["board"] else "",
            "board_name": r["board"].name if r["board"] else "",
            "created_at": r["post"].created_at.isoformat(),
            "updated_at": r["post"].updated_at.isoformat() if r["post"].updated_at else None,
            "reply_count": r["reply_count"],
            "like_count": r["like_count"],
        }
        for r in results
    ]


@app.get("/api/recent")
def api_recent(limit: int = 10, db: Session = Depends(get_db)):
    results = crud.get_recent_posts(db, limit=limit)
    return [
        {
            "id": r["post"].id, "title": r["post"].title, "author": r["post"].author,
            "board_slug": r["board"].slug if r["board"] else "",
            "board_name": r["board"].name if r["board"] else "",
            "created_at": r["post"].created_at.isoformat(),
            "updated_at": r["post"].updated_at.isoformat() if r["post"].updated_at else None,
            "reply_count": r["reply_count"],
            "like_count": r["like_count"],
        }
        for r in results
    ]


@app.get("/api/last-activity")
def api_last_activity(db: Session = Depends(get_db)):
    data = crud.get_last_activity(db)
    def _iso(dt) -> str | None:
        return dt.isoformat() if dt else None
    return {
        "last_post_at": _iso(data["last_post_at"]),
        "last_updated_at": _iso(data["last_updated_at"]),
        "last_comment_at": _iso(data["last_comment_at"]),
        "last_like_at": _iso(data["last_like_at"]),
        "last_activity_at": _iso(data["last_activity_at"]),
    }
