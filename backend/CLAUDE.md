# Backend — CLAUDE.md

## Git 전략 (상세 내용: `git.md`)

### 브랜치 구조
- `main` — 배포용, 직접 commit 불가
- `develop` — 개발 merge 대상
- `feature/*` — 개인 작업 후 develop에 PR

### 브랜치 네이밍
```
type/#이슈번호-파트-작업명
예: feature/#7-be-login
    fix/#12-be-token-expire
```

### 커밋 메시지 형식
```
feat: 새로운 기능 추가 #이슈번호
fix: 버그 수정 #이슈번호
refactor: 코드 구조 개선 #이슈번호
style: 포맷/들여쓰기 등 (로직 변경 없음)
chore: 패키지 설치, 환경설정, 빌드
docs: README, 주석 등 문서 작업
test: 테스트 코드 추가 및 수정
remove: 파일 또는 코드 삭제 #이슈번호
```

### 작업 흐름 요약
1. **GitHub 웹** — Issue 생성 (`[BE] 작업 설명`)
2. **터미널** — `develop` pull → feature 브랜치 생성
3. **터미널** — 작업 → 커밋
4. **터미널** — `fetch` → `merge origin/develop` → `push`
5. **GitHub 웹** — PR 생성 (`base: develop`, `closes #이슈번호`)
6. **GitHub 웹** — 리뷰 → Merge → 리모트 브랜치 삭제
7. **터미널** — `develop` pull → 로컬 브랜치 삭제

> PR 생성 시 CodeRabbit이 자동으로 AI 코드 리뷰 코멘트를 달아줌.
