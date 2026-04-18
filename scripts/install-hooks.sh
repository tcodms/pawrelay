#!/bin/bash
# CLAUDE.md 규칙 검사 pre-commit 훅 설치
# 실행: bash scripts/install-hooks.sh

REPO_ROOT=$(git rev-parse --show-toplevel)
HOOK_PATH="$REPO_ROOT/.git/hooks/pre-commit"

cat > "$HOOK_PATH" << 'HOOK'
#!/bin/bash
python3 scripts/check_claude_rules.py || python scripts/check_claude_rules.py
HOOK

chmod +x "$HOOK_PATH"
echo "✅ pre-commit 훅 설치 완료"
