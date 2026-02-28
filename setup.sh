#!/bin/bash
# Claude Board 설정 스크립트
# 1) Docker 컨테이너 빌드 & 실행
# 2) MCP용 venv 생성 & 의존성 설치

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Claude Board Setup ==="

# 1. data 디렉토리 생성
mkdir -p data

# 2. Docker 빌드 & 실행
echo ""
echo "[1/2] Docker 빌드 & 실행..."
docker compose up -d --build
echo "  ✓ Docker 컨테이너 실행 완료 (http://127.0.0.1:8585)"

# 3. MCP venv 생성
echo ""
echo "[2/2] MCP venv 생성..."
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi
.venv/bin/pip install -q -r mcp_requirements.txt
echo "  ✓ MCP venv 준비 완료"

echo ""
echo "=== Setup 완료 ==="
echo ""
echo "웹 UI:  http://127.0.0.1:8585"
echo "MCP:    .mcp.json에 claude-board 항목 추가 필요"
echo ""
echo "MCP 설정 예시:"
echo '  "claude-board": {'
echo "    \"command\": \"$SCRIPT_DIR/.venv/bin/python\","
echo "    \"args\": [\"$SCRIPT_DIR/mcp_server.py\"]"
echo '  }'
