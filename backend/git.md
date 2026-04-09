## 브랜치

- main : 배포용 브랜치(중간, 기말 발표에 사용) - 직접 commit 불가
- develop: 개발 merge
- feature: 각자 본인 feature 브랜치에서 작업 후 develop에 PR

## Commit Message Prefix

feat 새로운 기능 추가
fix 버그 수정
refactor 기능 변경 없이 코드 구조 개선
style 포맷, 들여쓰기, 세미콜론 등 (로직 변경 없음)
chore 패키지 설치, 환경설정, 빌드 관련
docs README, 주석 등 문서 작업
test 테스트 코드 추가 및 수정
remove 파일 또는 코드 삭제

```bash
feat: 로그인 API 구현 #7
fix: 토큰 만료 시 500 에러 수정 #12
refactor: 인증 미들웨어 구조 개선 #7
chore: eslint 설정 추가
docs: API 명세 README 업데이트
remove: 사용하지 않는 유틸 함수 삭제 #9
```

## Issue & Pull Request 사용

### 템플릿

`.github` 에 저장 → 자동으로 양식 불러오게 함

.github/
├── ISSUE_TEMPLATE/
│ ├── [feature.md]
│ └── [bugfix.md]
└── pull_request_template.md

### Issue 제목 / 브랜치 이름

| Issue 제목                     | 브랜치 이름                |
| ------------------------------ | -------------------------- |
| `[BE] 로그인 API 구현`         | `feature/#7-be-login`      |
| `[FE] 로그인 페이지 UI 구현`   | `feature/#8-fe-login`      |
| `[BE] 토큰 만료 500 에러 수정` | `fix/#12-be-token-expire`  |
| `[FE] 메인 대시보드 구현`      | `feature/#15-fe-dashboard` |
| `[AI] 추천 모델 연동`          | `feature/#21-ai-recommend` |

- Issue 제목 → `[파트] 작업 설명`
- 브랜치 이름 → `type/#이슈번호-파트-작업명`

```bash
터미널에서 하는 것        GitHub 웹에서 하는 것
─────────────────────    ─────────────────────
git add                  Issue 생성
git commit               PR 생성
git push                 코드 리뷰
git merge                Issue/PR 닫기
git branch               라벨 달기
```

## 전체 흐름

### 1. GitHub 웹 - Issue 생성

```
Issue 탭 → New Issue → Feature 템플릿 선택
제목: [BE] 로그인 API 구현
내용 작성 후 Submit → #7 번호 확인
```

---

### 2. 터미널 - 브랜치 생성

```bash
# develop 최신 상태로 업데이트
git checkout develop
git pull origin develop

# 브랜치 생성
git checkout -b feature/#7-be-login
```

---

### 3. 터미널 - 작업 & 커밋

```bash
# 코드 작업 후
git add .
git commit -m "feat: 로그인 API 구현 #7"

# 작업이 길어지면 커밋 여러 번 해도 됨
git commit -m "feat: JWT 토큰 발급 구현 #7"
git commit -m "feat: Google 소셜 로그인 추가 #7"
git commit -m "fix: 토큰 만료 예외처리 #7"
```

---

### 4. 터미널 - Push 전 충돌 확인

```bash
# develop에 다른 팀원이 올린 내용 가져오기
git fetch origin

# 내 브랜치에 develop 변경사항 반영
git merge origin/develop

# 충돌(conflict)이 있으면 파일 열어서 수동 해결 후
git add .
git commit -m "merge: develop 충돌 해결"

# push
git push origin feature/#7-be-login
```

```bash
git pull origin develop
# = git fetch origin + git merge origin/develop
```

---

### 5. GitHub 웹 - PR 생성

```
Pull requests 탭 → New Pull Request
base: develop  ←  compare: feature/#7-be-login

제목: [BE] 로그인 API 구현
템플릿 내용 작성:
  - closes #7
  - 작업 내용 기술
  - 리뷰어 지정
Submit
```

---

### 6. GitHub 웹 - 코드 리뷰 & Merge

```
팀원이 리뷰 후 Approve
→ Merge Pull Request 클릭
→ Delete branch 클릭 (리모트 브랜치 삭제)
→ Issue #7 자동 close 확인
```

---

### 7. 터미널 - 로컬 브랜치 정리

```bash
# develop으로 이동 후 최신화
git checkout develop
git pull origin develop

# 로컬 브랜치 삭제
git branch -d feature/#7-be-login
```

---

## 한눈에 보기

```
웹   | Issue 생성 (#7)
터미널 | develop pull → 브랜치 생성
터미널 | 작업 → 커밋
터미널 | fetch → merge → push
웹   | PR 생성 (closes #7)
웹   | 리뷰 → Merge → 리모트 브랜치 삭제
터미널 | develop pull → 로컬 브랜치 삭제
```

## CodeRabbit

PR 올리면 AI가 자동으로 코드 리뷰 코멘트 달아주는 툴

### CodeRabbit 세팅 방법

**1. GitHub 웹**

```
coderabbit.ai 접속
→ Sign in with GitHub
→ 팀 레포 선택 후 Install
```

**2. 이후 PR 올리면 자동으로**

```
- 코드 변경사항 분석
- 버그 가능성 있는 부분 코멘트
- 개선 제안
- PR 요약 작성
```

무료 범위

```
public 레포  → 무료
private 레포 → 유료 (팀 프로젝트면 public으로 하거나 학생 플랜 확인)
```
