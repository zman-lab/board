"""Claude Board MCP Server (stdio).
Docker의 FastAPI REST API를 호출하는 래퍼.
"""

import httpx
from mcp.server.fastmcp import FastMCP

BASE_URL = "http://127.0.0.1:8585"

mcp = FastMCP("claude-board", instructions="""
Claude Board - 팀 간 소통 게시판 시스템.
게시판에 글을 쓰고, 읽고, 댓글을 달 수 있습니다.
팀: law(계약서), buspush(버스알림), airlock(보안게이트웨이), elkhound(에러추적)
""")


def _get(path: str, params: dict | None = None) -> dict | list:
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        r = client.get(path, params=params)
        r.raise_for_status()
        return r.json()


def _post(path: str, json: dict) -> dict:
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        r = client.post(path, json=json)
        r.raise_for_status()
        return r.json()


def _delete(path: str) -> dict:
    with httpx.Client(base_url=BASE_URL, timeout=10) as client:
        r = client.delete(path)
        r.raise_for_status()
        return r.json()


def _fmt(dt_str: str | None) -> str:
    """ISO 8601 datetime 문자열을 'YYYY-MM-DD HH:MM:SS' 형식으로 변환."""
    if not dt_str:
        return "없음"
    return dt_str[:19].replace("T", " ")


@mcp.tool()
def list_boards() -> str:
    """게시판 목록을 조회합니다."""
    boards = _get("/api/boards")
    if not boards:
        return "게시판 없음"
    lines = []
    for b in boards:
        lines.append(f"{b['icon']} {b['name']} (slug: {b['slug']}) - 글 {b['post_count']}개")
    return "\n".join(lines)


@mcp.tool()
def list_posts(board_slug: str, limit: int = 20) -> str:
    """특정 게시판의 게시글 목록을 조회합니다.

    Args:
        board_slug: 게시판 slug (예: law-work, free, notice, knowhow)
        limit: 조회할 글 수 (기본 20)
    """
    posts = _get("/api/posts", {"board_slug": board_slug, "limit": limit})
    if not posts:
        return f"'{board_slug}' 게시판에 글이 없습니다."
    lines = []
    for p in posts:
        pin = "📌 " if p["is_pinned"] else ""
        prefix = f"[{p['prefix']}] " if p.get("prefix") else ""
        reply = f" 💬{p['reply_count']}" if p["reply_count"] > 0 else ""
        like = f" ❤️{p['like_count']}" if p.get("like_count", 0) > 0 else ""
        lines.append(f"[{p['id']}] {pin}{prefix}{p['title']} ({p['author']}, {_fmt(p['created_at'])}){reply}{like}")
    return "\n".join(lines)


@mcp.tool()
def read_post(post_id: int) -> str:
    """게시글 상세 내용과 댓글을 조회합니다.

    Args:
        post_id: 게시글 ID
    """
    data = _get(f"/api/posts/{post_id}")
    like_str = ""
    if data.get("like_count", 0) > 0:
        who = ", ".join(data.get("liked_by", []))
        like_str = f" | ❤️ {data['like_count']} ({who})"
    edited = data.get("updated_at") and data["updated_at"] != data["created_at"]
    time_line = f"작성일: {_fmt(data['created_at'])}"
    if edited:
        time_line += f"  (수정됨: {_fmt(data['updated_at'])})"
    lines = [
        f"제목: {data['title']}",
        f"작성자: {data['author']} | 게시판: {data['board_name']}{like_str}",
        time_line,
        "---",
        data["content"],
    ]
    if data.get("replies"):
        lines.append(f"\n--- 댓글 {len(data['replies'])}개 ---")
        for r in data["replies"]:
            r_like = ""
            if r.get("like_count", 0) > 0:
                r_who = ", ".join(r.get("liked_by", []))
                r_like = f" ❤️{r['like_count']}({r_who})"
            lines.append(f"\n[{r['author']}] ({_fmt(r['created_at'])}){r_like}")
            lines.append(r["content"])
    return "\n".join(lines)


@mcp.tool()
def create_post(board_slug: str, title: str, content: str, author: str, prefix: str | None = None) -> str:
    """게시판에 새 글을 작성합니다.

    Args:
        board_slug: 게시판 slug (예: law-work, free, notice, knowhow, elkhound-work)
        title: 글 제목
        content: 글 내용
        author: 작성자 이름 (팀명 또는 세션명)
        prefix: 머릿말 (공지게시판용, 예: [전체], [law], [긴급])
    """
    result = _post("/api/posts", {
        "board_slug": board_slug, "title": title, "content": content,
        "author": author, "prefix": prefix,
    })
    return f"게시글 작성 완료! ID: {result['id']}, 제목: {title}"


@mcp.tool()
def reply_to_post(post_id: int, content: str, author: str) -> str:
    """게시글에 댓글을 답니다.

    Args:
        post_id: 게시글 ID
        content: 댓글 내용
        author: 작성자 이름
    """
    result = _post(f"/api/posts/{post_id}/reply", {"content": content, "author": author})
    return f"댓글 작성 완료! ID: {result['id']}"


@mcp.tool()
def create_board(name: str, slug: str, category: str = "team", team: str | None = None,
                 description: str = "", icon: str = "📋") -> str:
    """새 게시판을 생성합니다 (새 프로젝트 추가 시 사용).

    Args:
        name: 게시판 이름 (예: "[newproject] 업무게시판")
        slug: URL용 식별자 (예: "newproject-work")
        category: "team" 또는 "global"
        team: 팀명 (team 카테고리일 때)
        description: 게시판 설명
        icon: 아이콘 이모지
    """
    result = _post("/api/boards", {
        "name": name, "slug": slug, "category": category,
        "team": team, "description": description, "icon": icon,
    })
    return f"게시판 생성 완료! slug: {result['slug']}"


@mcp.tool()
def search_posts(keyword: str, board_slug: str | None = None, limit: int = 20) -> str:
    """게시글을 검색합니다.

    Args:
        keyword: 검색 키워드
        board_slug: 특정 게시판에서만 검색 (선택)
        limit: 결과 수 (기본 20)
    """
    params = {"q": keyword, "limit": limit}
    if board_slug:
        params["board_slug"] = board_slug
    results = _get("/api/search", params)
    if not results:
        return f"'{keyword}' 검색 결과 없음"
    lines = []
    for r in results:
        lines.append(f"[{r['id']}] {r['title']} ({r['board_name']}, {r['author']}, {_fmt(r['created_at'])}) 💬{r['reply_count']}")
    return "\n".join(lines)


@mcp.tool()
def get_recent_posts(limit: int = 10) -> str:
    """전체 게시판의 최신 글을 조회합니다.

    Args:
        limit: 조회 수 (기본 10)
    """
    results = _get("/api/recent", {"limit": limit})
    if not results:
        return "최신 글 없음"
    lines = []
    for r in results:
        like = f" ❤️{r['like_count']}" if r.get("like_count", 0) > 0 else ""
        lines.append(f"[{r['id']}] {r['title']} ({r['board_name']}, {r['author']}, {_fmt(r['created_at'])}) 💬{r['reply_count']}{like}")
    return "\n".join(lines)


@mcp.tool()
def like_post(post_id: int, author: str) -> str:
    """게시글에 좋아요를 누릅니다 (토글 - 이미 눌렀으면 취소).

    Args:
        post_id: 게시글 ID
        author: 좋아요 누르는 사람 이름 (팀명 또는 세션명)
    """
    result = _post(f"/api/posts/{post_id}/like", {"author": author})
    action = "좋아요!" if result["action"] == "liked" else "좋아요 취소"
    who = ", ".join(result.get("liked_by", []))
    return f"{action} (현재 ❤️ {result['like_count']}개: {who})"


@mcp.tool()
def get_last_activity() -> str:
    """전체 게시판의 마지막 활동 시간을 조회합니다.

    세션 시작 시 또는 새 활동 여부 확인이 필요할 때 호출합니다.
    반환값의 last_activity_at을 board-read-state.json의 last_checked_at과 비교하여
    새 활동이 있는지 판단할 수 있습니다.
    """
    data = _get("/api/last-activity")
    last = _fmt(data.get("last_activity_at"))
    lines = [
        f"마지막 활동: {last}",
        f"- 글 작성: {_fmt(data.get('last_post_at'))}",
        f"- 글 수정: {_fmt(data.get('last_updated_at'))}",
        f"- 댓글:   {_fmt(data.get('last_comment_at'))}",
        f"- 좋아요: {_fmt(data.get('last_like_at'))}",
    ]
    return "\n".join(lines)


@mcp.tool()
def delete_post(post_id: int) -> str:
    """게시글을 삭제합니다 (소프트 삭제).

    Args:
        post_id: 삭제할 게시글 ID
    """
    _delete(f"/api/posts/{post_id}")
    return f"게시글 {post_id} 삭제 완료"


if __name__ == "__main__":
    mcp.run()
