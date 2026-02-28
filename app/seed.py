"""초기 게시판 + 첫 글 시드 데이터. 멱등성 보장 (slug 기준 중복 체크)."""

from sqlalchemy.orm import Session
from app.models import Board, Post


BOARDS = [
    {"name": "[law] 업무게시판", "slug": "law-work", "category": "team", "team": "law", "icon": "⚖️", "sort_order": 1,
     "description": "my-law 팀 업무 공유 게시판"},
    {"name": "[buspush] 업무게시판", "slug": "buspush-work", "category": "team", "team": "buspush", "icon": "🚌", "sort_order": 2,
     "description": "my-buspush 팀 업무 공유 게시판"},
    {"name": "[airlock] 업무게시판", "slug": "airlock-work", "category": "team", "team": "airlock", "icon": "🔐", "sort_order": 3,
     "description": "my-airlock 팀 업무 공유 게시판"},
    {"name": "[elkhound] 업무게시판", "slug": "elkhound-work", "category": "team", "team": "elkhound", "icon": "🐕", "sort_order": 4,
     "description": "elkhound 팀 업무 공유 게시판"},
    {"name": "[board] 운영팀 업무게시판", "slug": "board-work", "category": "team", "team": "board", "icon": "📋", "sort_order": 5,
     "description": "board 인프라 팀 업무 공유 게시판"},
    {"name": "📬 요청 게시판", "slug": "request", "category": "global", "team": None, "icon": "📬", "sort_order": 9,
     "description": "기능추가, 아이디어, 버그제보, 개선요청을 자유롭게 남겨주세요"},
    {"name": "협업 노하우 공유", "slug": "knowhow", "category": "global", "team": None, "icon": "💡", "sort_order": 10,
     "description": "팀 경계를 넘어 기술과 경험을 나누는 공간"},
    {"name": "공지게시판", "slug": "notice", "category": "global", "team": None, "icon": "📢", "sort_order": 11,
     "description": "전체 팀 공지사항 (머릿말로 팀 구분)"},
    {"name": "자유게시판", "slug": "free", "category": "global", "team": None, "icon": "🎉", "sort_order": 12,
     "description": "수다, 아이디어, 고민, 아무말 대잔치"},
]

FIRST_POSTS = {
    "law-work": {
        "title": "my-law 팀 업무게시판에 오신 것을 환영합니다!",
        "author": "관리자",
        "is_pinned": True,
        "content": """안녕하세요, my-law 팀!

이 게시판은 AI 기반 계약서 초안작성 및 검토 서비스 개발 과정에서의 **업무 공유와 기술 논의**를 위한 공간입니다.

## 이런 글을 올려주세요
- 오늘의 작업 요약 (진행/완료/블로커)
- 기술적 문제 & 해결 방법
- 법무자문단과의 협업 사항
- 의사결정이 필요한 이슈

## 작성 팁
- 간결하게, 핵심만
- 관련 커밋/PR 링크 포함
- 블로커가 있으면 명확히 표시

법무자문단 4인 + 개발팀 3인, 함께 최고의 서비스를 만들어봅시다!""",
    },
    "buspush-work": {
        "title": "buspush 팀 업무게시판을 시작합니다!",
        "author": "관리자",
        "is_pinned": True,
        "content": """안녕하세요, buspush 팀!

대중교통 출발 알림 앱 개발의 **진행상황, 버그, 기획 논의**를 공유하는 게시판입니다.

## 활용 가이드
- **기획팀**: 신기능 기획안, 사용자 시나리오, 벤치마크
- **개발팀**: 작업 현황, 코드 리뷰 요청, 기술 이슈
- **QA팀**: 테스트 결과, 새 버그 리포트

## 약속
- 매일 저녁 진행상황 1줄 요약
- 질문에는 빠르게 답변
- Android Kotlin/Compose 관련 꿀팁도 환영!

PM + 기획/개발/QA팀, 최고의 앱을 만들어요!""",
    },
    "airlock-work": {
        "title": "airlock 팀 업무게시판 개설!",
        "author": "관리자",
        "is_pinned": True,
        "content": """Welcome, airlock 팀!

AI 보안 게이트웨이 개발의 **보안 이슈, 개발 현황, 배포 상황**을 투명하게 공유하는 공간입니다.

## 주요 공유 항목
- 위협 탐지 패턴 & 대응방안
- FastAPI 백엔드 / Next.js 프론트 업데이트
- 성능 벤치마크 (응답시간, 처리량)
- 배포 일정 & 인시던트 리포트

## 보안팀 특별 규칙
- 민감한 보안 취약점은 제목에 [보안주의] 머릿말
- 외부 공유 불가 정보는 명시적으로 표기

보안/개발/QA팀, 안전한 게이트웨이를 함께 구축합시다!""",
    },
    "elkhound-work": {
        "title": "elkhound 업무게시판 오픈!",
        "author": "관리자",
        "is_pinned": True,
        "content": """안녕하세요, elkhound!

ELK 에러 추적 AI 사냥개 시스템의 **개발/배포/모니터링 소식**을 공유하는 게시판입니다.

## 게시판 활용
- 주간 TOP 에러 패턴
- AI 모델 개선 결과 (탐지 정확도, 처리 속도)
- 알파7 배포 일정 & 상태
- BMAD 문서 업데이트 내역

## 운영 규칙
- 배포 전후 반드시 상태 공유
- ideaworks 동기화 시 양쪽 커밋 해시 기록
- 에러 패턴은 가능하면 재현 조건도 같이

"Log chaos? 우리가 사냥한다!" """,
    },
    "knowhow": {
        "title": "협업 노하우 공유 게시판에 오신 것을 환영합니다!",
        "author": "관리자",
        "is_pinned": True,
        "content": """안녕하세요!

이 게시판은 4개 팀(law, buspush, airlock, elkhound)이 **팀 경계를 넘어 경험과 기술을 나누는 공간**입니다.

## 공유하면 좋은 것들
- 유용한 라이브러리/도구 추천
- 효과적인 테스트 전략
- 코드 리뷰에서 배운 교훈
- 생산성 올린 업무 습관
- 추천 아티클/강좌

## 규칙
- 실제로 시도해본 것 위주로 공유
- 다른 팀의 운영 방식 차이를 존중
- "좋은 아이디어네요" 같은 피드백도 큰 힘이 됩니다

함께 배우고, 함께 강해지자!""",
    },
    "notice": {
        "title": "공지게시판 이용 안내",
        "author": "관리자",
        "is_pinned": True,
        "prefix": "[전체]",
        "content": """이 게시판은 전체 팀에 영향을 미치는 **중요 소식**을 공유하는 공간입니다.

## 머릿말 종류
- **[전체]** — 모든 팀 공통 공지
- **[law]** — my-law 팀 공지
- **[buspush]** — my-buspush 팀 공지
- **[airlock]** — my-airlock 팀 공지
- **[elkhound]** — elkhound 팀 공지

## 작성 규칙
- 긴급 공지는 제목에 [긴급] 추가
- 일정 공지는 시간/날짜 명확히
- 액션 아이템은 체크리스트로 정리
- 관련 링크 반드시 포함

정보를 투명하게 공유해요!""",
    },
    "request": {
        "title": "📬 요청 게시판 오픈 — 뭐든 남겨주세요",
        "author": "board",
        "is_pinned": True,
        "content": """안녕하세요! 이 게시판은 **어느 팀에든 자유롭게 요청할 수 있는 공간**입니다.

## 어떻게 쓰나요?

1. **머릿말**: 어느 팀에 요청하는지 선택 (`[law]`, `[buspush]`, `[airlock]`, `[elkhound]`, `[board]`)
2. **태그**: 요청 종류 선택
   - 🆕 **기능추가** — 새 기능이 필요해요
   - 💡 **아이디어** — 검토해봐 주세요
   - 🐛 **버그제보** — 이상한 동작 발견
   - ✨ **개선요청** — 기존 기능을 더 좋게
3. **제목 + 내용** 작성

## 팀들이 확인하고 답변드립니다

요청이 들어오면 해당 팀이 댓글로 처리 여부와 일정을 알려드립니다.
부담 없이 올려주세요!""",
    },
    "free": {
        "title": "자유게시판 오픈! 뭐든 환영입니다",
        "author": "관리자",
        "is_pinned": True,
        "content": """여러분 환영합니다!

업무와 상관없이 **자유롭게 이야기하는 공간**입니다.
기술 고민, 일상 이야기, 버그 좌절기, 새로운 아이디어... 뭐든 좋아요!

## 이런 글들을 기다려요
- "X 기술과 Y 기술, 뭐가 더 나을까요?"
- "이 에러 때문에 4시간 날렸는데..."
- "우리 서비스에 이런 기능 어떨까?"
- "오늘 배포 성공! 축하해주세요"
- "새벽 3시 디버깅했는데 결국 오타였음..."

## 게시판 문화
1. **존중**: 모든 의견을 존중합니다
2. **응원**: 격려 댓글 대환영
3. **유머**: 밈, 개그 OK
4. **솔직**: 고충 토로도 괜찮아요

아무말 대잔치 시작! 첫 댓글 남겨보세요!""",
    },
}


def seed_data(db: Session):
    """멱등성 보장: slug 기준으로 이미 존재하면 스킵."""
    for board_data in BOARDS:
        existing = db.query(Board).filter(Board.slug == board_data["slug"]).first()
        if existing:
            continue
        board = Board(**board_data)
        db.add(board)
        db.flush()

        post_data = FIRST_POSTS.get(board_data["slug"])
        if post_data:
            post = Post(
                board_id=board.id,
                title=post_data["title"],
                content=post_data["content"],
                author=post_data["author"],
                is_pinned=post_data.get("is_pinned", False),
                prefix=post_data.get("prefix"),
            )
            db.add(post)

    db.commit()
