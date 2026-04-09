# PawRelay — CLAUDE.md

유기동물 릴레이 이동봉사 플랫폼. LLM 기반 자정 배치 매칭으로 보호소-봉사자를 연결한다.

---

## 팀 역할 분담

| 역할 | 담당 디렉터리 | 주요 책임 |
|------|--------------|----------|
| **Frontend** | `frontend/` | Next.js PWA, 보호소 대시보드, 봉사자 앱, 챗봇 UI |
| **Backend** | `backend/` | FastAPI REST API, WebSocket, 인증, 릴레이 트래킹 |
| **AI** | `ai/` | LLM Matching Engine, Geocoding, Anomaly Detector |

> 인터페이스는 `docs/api-spec.md`가 단일 진실 소스다. API 변경 시 반드시 사전 공지.

---

## 기술 스택

### Frontend (`frontend/`)
- **Next.js** — 웹 + PWA 단일 코드베이스
  - `/dashboard/*` — 보호소 (데스크탑)
  - `/volunteer/*` — 봉사자 (모바일 PWA)
- `next-pwa` — Service Worker, 홈화면 설치
- **Web Push API** — 인앱 푸시 (iOS 16.4+, PWA 설치 필요)
- **카카오맵 API** — 지도 렌더링 전용 (프론트 only)
- **WebSocket** — 보호소 대시보드 + 입양자 페이지 실시간 업데이트

### Backend (`backend/`)
- **FastAPI (Python)** — 비동기 REST API + WebSocket
- **PostgreSQL + PostGIS** — 메인 DB + 지리 필터링
- **Redis** — WebSocket Pub/Sub, 세션, Refresh Token 저장
- JWT: Access Token 15분 / Refresh Token 7일 (httpOnly 쿠키)

### AI (`ai/`)
- **Claude API** (`claude-sonnet-4-6`) — 기본 LLM
- **OpenAI API** (`gpt-4o`) — 전환 가능 (추상화 레이어 사용)
- **카카오맵 Geocoding API** — 백엔드에서 호출 (API 키 노출 방지)

---

## 디렉터리 구조 (목표)

```
pawrelay/
├── frontend/          # Next.js
│   ├── app/
│   │   ├── dashboard/ # 보호소 웹
│   │   └── volunteer/ # 봉사자 PWA
│   └── ...
├── backend/           # FastAPI
│   ├── routers/       # auth, posts, volunteers, matching, relay, chatbot, admin
│   ├── models/        # SQLAlchemy ORM
│   ├── services/      # 비즈니스 로직
│   └── ...
├── ai/                # LLM 관련
│   ├── matching/      # Matching Engine (3단계)
│   ├── providers/     # ClaudeProvider, OpenAIProvider
│   └── ...
└── docs/
    ├── design.md      # 설계 문서
    └── api-spec.md    # API 명세 (확정본)
```

---

## 핵심 비즈니스 로직

### 매칭 플로우 (자정 배치)
1. `transport_posts` 에서 `status=recruiting` 공고 전체 수집 (날짜 무관, 매일 재시도)
2. **1단계 SQL**: 각 공고의 `scheduled_date`와 `available_date`가 일치하는 `volunteer_schedules` 수집
   - `post_id`가 해당 공고인 봉사자는 가중치 높게 처리 (직접 지원)
   - `post_id=NULL`인 봉사자는 날짜·동선 기준으로 전체 공고 대상
   - PostGIS로 경로 근접성·동물크기 필터 (수백→수십 건)
3. **2단계 Python**: 인계 시간 간격 검증 (`HANDOVER_BUFFER = 30분`), 연결 가능 체인만 남김
4. **3단계 LLM**: 최적 체인 선택 + `matching_reason` 한국어 생성
5. 보호소 확인(24시간) → 봉사자 수락(24시간) → 매칭 확정
6. 매칭 확정 시 `volunteer_schedules.status = matched` → 다음 배치 대상에서 제외

### 챗봇 (자연어 기반 LLM 파이프라인)
봉사자의 자유 입력을 LLM이 파싱·정규화해 DB 저장 형태로 변환. 누락 필드는 Multi-turn으로 추가 질문.
```
봉사자 자유 입력 → LLM 파싱·정규화 → 누락 필드 추가 질문(Multi-turn) → DB 저장
```
- `post_id` 있는 진입: LLM이 공고 요구사항을 인지한 상태로 시작, 불필요한 질문 생략
- 세션: Redis 저장, FE는 `sessionStorage`에 `session_id` 보관

### 인계 확인 (6자리 코드)
- 출발 당일 00:00부터 코드 노출
- 양쪽 모두 입력 시 segment 완료
- 폴백: 앞 구간 봉사자가 인계 요청 → 뒷 구간 봉사자 승인

### share_token (입양자 조회)
- UUID v4, 로그인 불필요
- 공개 필드: 체크포인트 위치, 인계 타임라인, 현재 구간 정보
- 봉사자 실명·연락처 비공개
- WebSocket: `ws://api/ws?share_token=xxxx`

---

## 공통 코딩 규칙

- 함수는 20줄 이하로 유지
- 변수명은 의미가 명확하게 (축약 금지)
- 주석보다 코드 자체가 읽기 쉽도록

### Backend (Python)
- 비즈니스 로직은 `services/`에, 라우터는 얇게 유지
- 에러 응답: `{"error": "ERROR_CODE"}` 형식 통일
- 페이지네이션: `?page=1&limit=20` / 응답: `{data, total, page, limit}`
- Geocoding은 항상 백엔드에서 처리 (API 키 보호)

### Frontend (TypeScript)
- API 401 수신 시 자동으로 `/auth/refresh` 호출 (인터셉터 필수)
- WebSocket 재연결 시 `GET /notifications/unread` 호출
- GPS 거부 시: latitude/longitude null로 전송 + 사용자에게 안내 메시지

### AI (Python)
- LLM 호출은 `LLMProvider` 추상화 레이어 통해서만
- JSON 파싱 실패 시 재시도 최대 2회, 이후 관리자 알림
- LLM에게 수학 계산 시키지 않기 (체인 시간 검증은 Python 알고리즘 담당)

---

## LLM Provider 추상화

```python
# ai/providers/base.py
class LLMProvider:
    async def complete(self, prompt: str) -> str: ...

class ClaudeProvider(LLMProvider): ...   # claude-sonnet-4-6
class OpenAIProvider(LLMProvider): ...  # gpt-4o

# 환경변수: LLM_PROVIDER=claude | openai
```

---

## 주요 데이터 모델 요약

```
users               — id, email, role (shelter|volunteer|admin), account_status
shelter_profiles    — user_id, name, business_registration_number, verified_at
volunteer_profiles  — user_id, vehicle_available, max_animal_size, activity_regions
transport_posts     — id, shelter_id, status, animal_info, origin, destination, share_token
volunteer_schedules — id, volunteer_id, post_id(nullable), route(GEOMETRY), status
relay_chains        — transport_post_id, backup_candidates(JSONB), matching_reason, status
relay_segments      — chain_id, volunteer_id, segment_order, handover_code, status
checkpoints         — segment_id, type(departure|waypoint|arrival), latitude, longitude
notifications       — user_id, type, channel, payload(JSON), status
waypoints           — name, type(rest_area|train|bus|shelter), geom(PostGIS)
```

---

## 알림 채널 규칙

| 수신자 | 채널 |
|--------|------|
| 봉사자 (이동 중) | Web Push + 이메일 폴백 |
| 보호소 대시보드 | WebSocket |
| 입양자 조회 페이지 | WebSocket (share_token 채널) |
| PWA 미설치 / Push 거부 | 이메일 자동 대체 |

---

## MVP 범위

**MVP에 포함:**
- 챗봇 동선 등록 (자연어 LLM 파이프라인)
- LLM 배치 매칭 (자정 1회)
- 릴레이 트래킹 (체크포인트, 6자리 코드 인계)
- Web Push + WebSocket 알림
- 보호소 대시보드, 봉사자 PWA, 입양자 조회 페이지
- Admin: 보호소 승인, 사용자 관리

**Post-MVP (지금은 구현 금지):**
- LLM 기반 자연어 알림 메시지 생성
- 협력 보호소 연계 안내

---

## 참고 파일

- `docs/design.md` — 전체 설계 문서 (아키텍처, 플로우, 예외 처리)
- `docs/api-spec.md` — API 명세 확정본 (인터페이스 합의 결과)
