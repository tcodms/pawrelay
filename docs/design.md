# LLM 기반 릴레이 매칭을 활용한 유기동물 이동봉사 플랫폼 설계 문서

---

## 1. 개요

### 서비스 목적

유기동물 보호소와 개인 봉사자를 연결하여, LLM 기반 릴레이 매칭으로 장거리 이동봉사를 효율적으로 조율하는 플랫폼.

### 주요 사용자

- **보호소 담당자:** 이동 공고 등록 및 봉사자 관리 (웹 대시보드 중심)
- **봉사자:** 동선 등록 및 릴레이 참여 (PWA 모바일 중심)
- **입양자:** 이송 현황 실시간 조회 (로그인 불필요)

---

## 2. 기술 스택

### 프론트엔드

- **Next.js** (단일 코드베이스로 웹 + PWA 동시 지원)
  - `next-pwa`: Service Worker, 홈화면 설치, 오프라인 캐싱
  - `/dashboard/*`: 보호소 웹 대시보드 (데스크탑 최적화)
  - `/volunteer/*`: 봉사자 PWA (모바일 최적화)
  - Web Push API: 인앱 푸시 알림 (iOS 16.4+ 지원)
  - **iOS 제약:** 홈 화면에 추가(PWA 설치) 상태에서만 Push 권한 획득 가능
    - 봉사자 최초 가입 시 챗봇 도입부에 홈 화면 추가 방법 시각적 안내 (iOS/Android 분기)
    - 설치 미완료 상태에서 매칭 알림 발생 시 이메일로 자동 대체 발송
    - 서비스 가이드 페이지(FAQ)에 '앱 설치 방법' 섹션 포함

### 백엔드

- **FastAPI (Python):** LLM SDK 통합에 최적, async 지원
- **PostgreSQL + PostGIS:** 주 데이터베이스 + 지리적 근접 필터링
- **Redis:** 실시간 WebSocket Pub/Sub, 세션 관리

### 지도 및 위치 처리

- **카카오맵 API (Kakao Maps API):**
  - 입양자 이송 현황 조회 페이지: 현재 위치 마커 + 릴레이 경로 시각화
  - 봉사자 경로 안내 화면: 인계 장소까지 경로 안내
  - 프론트엔드에서만 사용 (지도 렌더링 용도)
- **Web Geolocation API (`navigator.geolocation`):**
  - 봉사자가 체크포인트 버튼을 누를 때 현재 스마트폰의 위도/경도 좌표 획득
  - 브라우저 기본 내장 기술 (별도 패키지 설치 불필요)
  - 획득한 좌표를 백엔드 체크포인트 API에 전송 → PostGIS `relay_segments` 기록

### 외부 서비스

- **Claude API (claude-sonnet-4-6) / OpenAI API:** LLM (추상화 레이어로 전환 가능)
- **SendGrid or AWS SES:** 이메일 알림
- 공공데이터포털 교통 API: 휴게소·기차역·버스터미널 위치 수집
- 공공데이터포털 APMS API: 전국 지자체 보호소 위치·연락처 수집

---

## 3. 전체 아키텍처

```
[Next.js - 웹/PWA]
        ↕ REST API / WebSocket
[FastAPI 백엔드]
    ├── Auth 모듈 (JWT + 이메일 인증 + 사업자번호 검증)
    ├── Transport 모듈 (이동 공고 관리)
    ├── Volunteer 모듈 (동선 등록, 게시판 지원)
    ├── LLM Orchestrator
    │     ├── Matching Engine       ← 자정 배치
    │     ├── Message Generator    ← 이벤트 기반
    │     └── Anomaly Detector     ← 스케줄러 + 이벤트
    ├── Batch Scheduler (매일 자정)
    ├── Relay Tracker (체크포인트, 인계 코드)
    └── Notification 모듈 (인앱 + 이메일 + 챗봇)
        ↕
[PostgreSQL] + [Redis] + [SendGrid/SES]
```

---

## 4. 봉사자 매칭 방식 (단일 챗봇 플로우)

모든 지원은 챗봇을 단일 진입점으로 사용한다. 게시판은 공고 탐색 용도로 유지하되, 지원 버튼을 누르면 항상 챗봇으로 이동한다.

### 진입 경로

- **게시판에서 진입:** "이 공고로 신청하기" 버튼 클릭 → 챗봇으로 이동 (post_id 자동 세팅)
- **직접 진입:** 챗봇 메뉴에서 동선 등록 시작

### 챗봇 입력 수집 (자연어 기반 LLM 파이프라인)

* **자연어(Free-text) 기반 동적 데이터 수집**
  정해진 순서대로 질문을 던지는 경직된 템플릿(상태 머신) 방식에서 벗어나,
  봉사자의 자유로운 대화형 발화를 LLM이 직접 처리함.

* **비정형 문장의 실시간 파싱(Parsing)**
  봉사자가 "나 내일 시간 비고 차는 없는데 고양이 봉사 가고 싶어"처럼 일상어로 입력하면,
  LLM이 문맥을 파악해 매칭에 필요한 핵심 파라미터(시간, 이동 수단, 선호 동물 등)를
  스스로 추출하고 구조화된 데이터로 변환함.

* **유연한 상호작용(Multi-turn) 지원**
  초기 입력 문장에서 필수 조건이 누락된 경우,
  LLM이 문맥을 유지한 채 "어느 지역을 선호하시나요?" 등
  필요한 정보만 자연스럽게 되물어(Multi-turn) 데이터를 동적으로 보완함.

게시판에서 post_id와 함께 진입한 경우, LLM이 이미 사용자가 선택한 공고의 요구사항을 인지한 상태로 대화를 시작함. 따라서 목적지나 일정 등을 묻는 불필요한 질문 과정을 생략하고, 봉사자의 개인 조건(차량 유무, 출발지) 등을 대화로 수집함.

> "다양한 형식의 자연어 입력을 LLM이 파싱·정규화하여 DB 저장 형태로 자동 변환하고, 누락된 필드는 챗봇이 자동으로 추가 질문을 생성해 수집함."

### LLM 파싱 플로우

```
봉사자 자유 입력
    ↓
LLM 파싱 + 정규화
    ↓
DB 저장 가능한 형태로 변환
    ↓
부족한 정보 있으면 → 챗봇이 자동으로 추가 질문 생성
    ↓
모든 필드 채워지면 → DB 저장
```

**정규화 예시**

| 봉사자 입력     | LLM 변환 결과              |
| --------------- | -------------------------- |
| "2024/3/25"     | `2024-03-25`               |
| "5월 5일"       | `2026-05-05`               |
| "광주광역시"    | `광주광역시`               |
| "서울"          | `서울특별시`               |
| "다음주 월요일" | `2026-04-06`               |
| "차 없어요"     | `vehicle_available: false` |
| "소형만 가능"   | `max_animal_size: small`   |

**차량 유무에 따른 인계 장소 추천**

- 차량 있음 → 휴게소, 기차역, 버스터미널 추천 가능
- 차량 없음 → 기차역 위주 추천, 최적 체인 구성 시 반영

### 매칭 플로우

1. 챗봇 입력 완료 → `volunteer_schedules` DB에 저장 (status: available, post_id nullable)
2. 매일 자정 배치 스케줄러 실행
   - post_id가 있는 일정은 해당 공고에 가중치를 높여 매칭
   - post_id가 없는 일정은 날짜·동선 기준으로 전체 공고 대상 매칭
3. LLM Matching Engine이 대기시간 최소·동선 이탈 최소 기준으로 최적 릴레이 체인 구성
4. 보호소 담당자에게 매칭 결과 확인 알림 → 24시간 내 승인/거절 가능
   - 12시간 경과 시 리마인더 알림 재발송
   - 미응답 시 자동 승인 처리 후 1시간 이내 취소 가능 (grace period)
5. 봉사자에게 매칭 제안 → 24시간 내 수락/거절 (기산점: 알림 발송 시각)
6. 확정 시 volunteer_schedules status → matched,
   아래 내용 포함한 매칭 확정 알림 발송
   - 담당 구간 (예: 광주 → 천안)
   - 인계 장소 추천 목록 (두 봉사자 activity_region 시/도 교차 지점 기준, waypoints에서 터미널·기차역·휴게소)
   - 카카오 오픈채팅 링크 (구간별 채팅방) — 장소 협의용
   - 카카오맵 링크
   - 파트너 연락처·6자리 인계 코드

**인계 장소 저장 방식**

- 매칭 확정 시 waypoints 1순위를 `relay_segments.dropoff_location`에 기본값으로 자동 저장
- 봉사자들이 오픈채팅에서 협의 후 다른 장소로 합의한 경우, 앞 구간 봉사자가 앱에서 장소 변경 가능
- 변경 시 상대 봉사자에게 인앱 알림 발송: "인계 장소가 [○○]로 변경되었습니다."
- 변경하지 않으면 기본값 그대로 사용
- 지연 신고·SOS는 `dropoff_location`이 아닌 현재 GPS 체크포인트 기반으로 동작하므로 기본값이어도 정상 작동

- 매칭된 봉사자는 다음 자정 배치 대상에서 자동 제외 (volunteer_schedules.status = matched)

### 배치 실패 처리

매칭 가능한 봉사자가 없거나 체인 구성이 불가능한 경우:

| 케이스      | 조건                              | 처리                                                                                                                           |
| ----------- | --------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 후보 없음   | SQL 필터 결과 0건                 | 공고 status 유지 (recruiting), 보호소 알림: "오늘 매칭 가능한 봉사자가 없었습니다."                                            |
| 체인 불성립 | 후보는 있으나 시간·구간 연결 불가 | 공고 status 유지 (recruiting), 보호소 알림: "봉사자가 있으나 구간 연결이 어렵습니다. 이동 날짜 또는 경로 조정을 고려해주세요." |

**날짜 임박 에스컬레이션 정책**

| 잔여 일수 | 처리                                    |
| --------- | --------------------------------------- |
| D-3 이상  | 매일 자정 재시도, 보호소에 실패 알림    |
| D-2       | 보호소 + 관리자 알림 ("수동 개입 필요") |
| D-1       | 관리자 긴급 알림 플래그                 |

---

## 5. LLM Orchestrator 상세 설계

### 5-1. Matching Engine (자정 배치) — 3단계 구조

[챗봇 필수 입력 정보](https://www.notion.so/3303b309eb54814cb445f059a3d516cd?pvs=21)

전체 데이터를 LLM에 직접 전달하면 컨텍스트 윈도우 초과 및 비용 문제가 발생하므로, 단계별로 후보를 압축한 뒤 LLM은 정성적 판단과 이유 생성에만 집중하는 3단계 구조를 사용한다.

> **역할 분리 원칙**
>
> - SQL: 조건에 맞는가? (이진 필터, DB 인덱스 활용)
> - 알고리즘: 체인 연결이 현실적으로 가능한가? (시간 계산, 그래프 탐색)
> - LLM: 가능한 체인 중 어떤 게 더 나은가? + 왜 이 조합인가? (정성적 판단 + 한국어 이유 생성)

**1단계: SQL 필터링 (PostGIS)**

- PostGIS로 경로 근접성, 날짜, 동물 크기, 차량 유무 조건을 한 번에 쿼리
- 수백 건 → 수십 건으로 압축

```sql
WHERE ST_DWithin(route, post.route, 50000)  -- 50km 이내 경로
  AND available_date = :date
  AND (vehicle = true OR animal_size = 'small')
  AND status = 'available'
```

**2단계: Python 알고리즘 — 체인 연결 가능성 검증**

- LLM은 시간 계산(수학)에 오류가 발생할 수 있으므로 알고리즘이 먼저 처리
- 인계 시간 간격이 현실적으로 가능한 체인만 남김 (이진 판단 Yes/No)
- 수십 건 → 5~10건으로 압축

```python
HANDOVER_BUFFER = timedelta(minutes=30)  # 최소 인계 대기 시간

def can_chain(prev_segment, next_segment) -> bool:
    return prev_segment.estimated_arrival + HANDOVER_BUFFER <= next_segment.departure_time

def build_valid_chains(candidates) -> list:
    # 그래프 탐색으로 연결 가능한 체인 조합만 반환
    ...
```

**3단계: LLM 최적 체인 선택 + 이유 생성**

- 연결 가능한 체인 5~10개 중 최적 1개 선택
- LLM이 잘하는 것에만 집중: 정성적 판단(동선 이탈, 봉사자 경험) + 한국어 이유 생성
- **입력:** 알고리즘이 검증한 후보 체인 목록 JSON
- **출력 예시:**

```json
{
  "chain": [
    { "volunteer_id": 1, "segment": "천안→수원", "handover_time": "14:30" },
    { "volunteer_id": 2, "segment": "수원→서울", "handover_time": "16:00" }
  ],
  "backup_candidates": { "segment_2": [5, 7] },
  "matching_reason": "두 봉사자의 동선이 수원에서 자연스럽게 이어져 대기 시간이 15분으로 최소화되었으며, 동선 이탈 없이 각자의 이동 경로 내에서 처리 가능한 최적 조합입니다."
}
```

- `matching_reason`은 보호소 대시보드 및 봉사자 매칭 상세 페이지에 노출
- **공고 1건씩 순차 처리** (전체 일괄 전송 금지)
- **안전장치:** JSON 파싱 실패 시 재시도 최대 2회 → 실패 시 관리자 알림

### 5-2. Geocoding 처리 (챗봇 동선 등록 시)

봉사자가 챗봇에서 텍스트로 출발지/목적지를 입력하면, 백엔드에서 좌표로 변환하여 저장한다.

```
챗봇 입력: "광주광역시", "천안시"
        ↓ 카카오맵 Geocoding API (백엔드 서버에서 호출)
좌표 변환: 광주 (126.85, 35.16) / 천안 (127.14, 36.80)
        ↓
DB 저장:
  route_description = "광주광역시 → 충남 천안시"   (TEXT)
  route = ST_MakeLine(                            (GEOMETRY)
            ST_SetSRID(ST_MakePoint(126.85, 35.16), 4326),
            ST_SetSRID(ST_MakePoint(127.14, 36.80), 4326)
          )
```

- Geocoding API 호출은 프론트가 아닌 **백엔드에서 처리** (API 키 노출 방지)
- 좌표 변환 실패 시 챗봇에서 입력 재요청 처리 필요

### 5-3. Message Generator (이벤트 기반) — Post-MVP

- MVP에서는 사전 정의된 템플릿 메시지 사용 (LLM 호출 없음)
- Post-MVP에서 LLM 기반 자연어 메시지 생성으로 전환
- 수신자 역할(봉사자/보호소/입양자)에 맞는 메시지 생성
- 인앱 토스트 + 이메일 본문 동시 생성

### 5-3.LLM API 추상화 레이어

```python
class LLMProvider:
    async def complete(self, prompt: str) -> str: ...

class ClaudeProvider(LLMProvider): ...   # claude-sonnet-4-6
class OpenAIProvider(LLMProvider): ...  # gpt-4o

# 환경변수로 전환
# LLM_PROVIDER=claude or openai
```

---

## 6. 핵심 데이터 모델

```
users
├── id, email, password_hash, role (shelter | volunteer | admin)
├── email_verified_at
└── account_status (active | suspended_30d | banned)

shelter_profiles
├── user_id (FK)
├── name, phone, email, operating_hours
├── business_registration_number
└── verified_at

volunteer_profiles
├── user_id (FK)
├── vehicle_available (bool), max_animal_size (small|medium|large)
└── activity_regions (배열)

transport_posts
├── id, shelter_id
├── status (recruiting | in_transit | completed | cancelled)
├── animal_info (name, size, photo, notes)
├── origin, destination, scheduled_date
└── share_token (UUID)

volunteer_schedules
├── id, volunteer_id, post_id (nullable) ← 게시판 진입 시 세팅, 가중치 힌트용
├── route_description  TEXT              ← "광주 → 천안" (화면 표시용)
├── route              GEOMETRY(LineString, 4326)  ← PostGIS 거리 계산용
├── available_date
├── origin_area, destination_area
├── max_animal_size
└── status (available | matched | expired)

relay_chains
├── id, transport_post_id
├── backup_candidates (JSONB) ← {"segment_order": [volunteer_id, ...]}
├── matching_reason (text)    ← LLM이 생성한 매칭 추천 사유
└── status (proposed | active | completed | broken)

relay_segments
├── id, chain_id, volunteer_id, segment_order
├── pickup_location, dropoff_location, scheduled_time
├── handover_code (6자리 일회용)
├── handover_code_given_at       ← 이전 봉사자가 코드 입력한 시각
├── handover_code_received_at    ← 다음 봉사자가 코드 입력한 시각
├── handover_method (code | qr | manual_approval) ← 실제 사용된 인계 방식
├── status (pending | accepted | in_progress | completed | needs_verification | no_show)
└── accepted_at, declined_at

checkpoints
├── id, segment_id, type (departure | waypoint | arrival)
├── latitude, longitude
└── recorded_at

notifications
├── id, user_id, type, channel (in_app | email | push)
├── payload (JSON), sent_at, read_at
├── status (pending | sent | failed)
├── retry_count (default 0)
└── transport_post_id (nullable)

volunteer_history
├── id, volunteer_id, segment_id
└── distance_km, completed_at

waypoints  ← 신규 추가
├── id, name, type (rest_area | train | bus | shelter)
├── address, phone (보호소만 해당)
├── geom (PostGIS geometry)
└── source (공공데이터포털 API 출처)
```

---

## 7. 릴레이 진행 플로우

### 정상 플로우

```
보호소 공고 등록 → share_token 자동 생성
    ↓
봉사자 챗봇 동선 입력 (or 게시판 직접 지원)
    ↓
LLM 배치 매칭 → relay_chains + relay_segments 생성
    ↓
봉사자 24시간 내 수락/거절
  └ 거절/미응답 → backup_candidates 순서대로 재알림
    ↓
출발 2시간 전 핑(Ping) 체크 발송
  └ 1시간 전 미응답 → 보호소 대시보드 주황색 경고
    ↓
이동 중 봉사자 체크포인트 버튼 클릭 (출발·거점·도착)
  └ 입양자 페이지 실시간 업데이트
    ↓
인계 확인 (6자리 코드 입력) → segment 완료 처리
    ↓
최종 도착 → 보호소·입양자 이메일 알림 + 봉사 내역 기록
```

### 예외 처리 플로우

**출발 전 노쇼:**

```
1구간 미출발 감지(취소 감지)
→ 체인 전체 해제
→ 대기 봉사자들 불발 알림
→ 공고 recruiting 복귀
```

**출발 후 노쇼 (긴급 모드):**

```
봉사자가 SOS 버튼 클릭
        ↓
해당 구간 거점 지역 확인
        ↓
activity_region = '광주광역시' 인 가용 봉사자 조회
        ↓
해당 구간 거점 지역 확인
        ↓
해당 봉사자들에게 긴급 이메일 알림 발송
"○○ 구간 긴급 봉사자 필요합니다. 참여 가능하신가요?"
        ↓
5분 대기
        ↓
응답 있으면 → 재매칭 완료
응답 없으면 → 보호소·관리자에게 알림
              "자동 재매칭 실패 — 수동 개입 필요"
        ↓
관리자 수동 처리
- 봉사자에게 임시 보호 안내 자동 발송
  (해당 구간 봉사자의 activity_region 시/도 단위 기준
   waypoints에서 type = 'shelter' 조회 → 안내)
  "대체 봉사자를 찾지 못했습니다.
   가장 가까운 보호소: [시/도 내 지자체 보호소명]
   📞 연락처
   동물을 이곳에 임시 보호 후 원래 보호소에 연락해주세요."
```

출발 전 자발적 취소:

인근 봉사자 재매칭 (실패 시 거점 인근 보호소로 안내)

**지연 신고:**

```
봉사자 [지연 알림] 버튼
→ 다음 구간 봉사자 + 보호소 즉시 알림
→ 입양자 조회 페이지 "지연 중" 상태 업데이트

[보호소 전화하기] 버튼
→ 직접 연락하여 보호소가 상황 중계
```

---

## 8. 알림 시스템

### 채널

| 채널      | 용도                                               | 구현                                                 |
| --------- | -------------------------------------------------- | ---------------------------------------------------- |
| Web Push  | 봉사자 알림 (이동 중, 앱 미실행 상태)              | Web Push API (PWA 설치 필요) / 미설치 시 이메일 대체 |
| WebSocket | 보호소 대시보드·입양자 조회 페이지 실시간 업데이트 | Redis Pub/Sub → WebSocket                            |
| 이메일    | 확정·종료·긴급·Web Push 폴백                       | SendGrid or AWS SES                                  |
| 챗봇 알림 | 인계 코드 전달                                     | 인앱 채팅 (봉사자 전용)                              |

> **채널 선택 원칙:** 봉사자는 이동 중 앱을 열어두지 않으므로 Web Push 사용. 보호소(데스크탑 대시보드)·입양자(조회 페이지 열람 중)는 WebSocket 사용.

### 발송 트리거

| 이벤트              | 수신자             | 채널                   |
| ------------------- | ------------------ | ---------------------- |
| 핑 체크             | 봉사자             | Web Push + 이메일 폴백 |
| 핑 확인             | 보호소 대시보드    | WebSocket              |
| 핑 미응답 경고      | 보호소 대시보드    | WebSocket              |
| 매칭 제안·확정      | 봉사자             | Web Push + 이메일      |
| 매칭 확정           | 보호소             | 이메일                 |
| 지연 신고           | 다음 봉사자        | Web Push + 이메일 폴백 |
| 지연 신고           | 보호소 대시보드    | WebSocket              |
| SOS                 | 인근 봉사자        | Web Push + 이메일      |
| SOS                 | 보호소 대시보드    | WebSocket              |
| 인계 장소 변경      | 상대 봉사자        | Web Push + 이메일 폴백 |
| 체크포인트 기록     | 입양자 조회 페이지 | WebSocket              |
| 봉사 시작·인계·종료 | 보호소 + 입양자    | 이메일                 |
| 노쇼 확정           | 해당 봉사자        | 이메일                 |

### WebSocket 설계

- **연결 단위:** 로그인한 사용자 1명당 1개 채널 (user_id 기준)
- **WebSocket 이벤트 목록:**

```
ping.confirmed           → 보호소 대시보드 초록 상태로 전환
ping.no_response         → 보호소 대시보드 주황 경고
delay.reported           → 보호소 대시보드 실시간 알림
sos.triggered            → 보호소 대시보드 실시간 알림
checkpoint.updated       → 입양자 조회 페이지 위치 실시간 업데이트
```

- **연결 끊김 처리:** 재연결 시 `GET /notifications/unread` 호출로 밀린 알림 수신 (폴링 폴백)

---

## 9. API 구조

```
/auth
  POST /signup/volunteer        # 봉사자 가입
  POST /signup/shelter          # 보호소 가입 (사업자번호 검증)
  POST /login
  POST /verify-email/{token}

/posts
  GET  /                        # 목록 (필터: 지역·날짜·동물크기)
  POST /                        # 공고 등록 (보호소)
  GET  /{id}
  PUT  /{id}                    # 수정 (보호소)
  GET  /public/{share_token}    # 입양자 조회 (인증 불필요)

/volunteers
  POST /schedules               # 챗봇 동선 등록 (post_id optional — 게시판 진입 시 포함)
  GET  /history                 # 봉사 내역

/matching
  POST /accept/{segment_id}     # 매칭 수락
  POST /decline/{segment_id}    # 매칭 거절

/relay
  POST /checkpoint              # 체크포인트 기록
  POST /handover/verify         # 인계 코드 입력
  POST /emergency/sos           # SOS 신고
  POST /emergency/delay         # 지연 알림

/shelter/dashboard              # 보호소 공고 현황 관리

/admin
  GET  /shelters/pending        # 승인 대기 중인 보호소 목록
  POST /shelters/{id}/approve   # 보호소 승인
  POST /shelters/{id}/reject    # 보호소 거절
  GET  /users                   # 사용자 검색
  POST /users/{id}/suspend      # 계정 정지
  POST /users/{id}/unsuspend    # 계정 정지 해제

/chatbot
  POST /message                 # 챗봇 메시지 송수신 (템플릿 상태 머신, LLM 미사용)
```

---

## 10. 전체 기능 목록

### 보호소

- 공고 등록 (출발지·목적지·날짜·동물 크기·특이사항·사진)
- 공고 등록 시 share_token 자동 생성
- 대시보드 (대기 중 / 매칭 진행 중 / 이송 중 / 완료 / 공고 수정)
- 마이페이지 연락처 관리 (전화번호, 이메일, 운영 시간)
- 사업자등록번호 (관리자 수동 인증)

### 봉사자

- 챗봇으로 동선·프로필 등록 (이동 경로, 날짜, 차량, 동물 크기)
- 게시판 직접 지원(챗봇으로 이동)
- 매칭 수락/거절 (24시간 기한)
- 출발 전 핑(Ping) 체크 응답
- 체크포인트 버튼 (출발·거점 도착·최종 도착)
- 인계 확인: 6자리 코드 수동 입력
- 지연 알림 버튼 + 보호소 전화하기 버튼
- SOS 긴급 신고 버튼
- 봉사 내역 아카이브 (완료 목록 + 총 이동 거리)
- 경로 안내 카카오맵 URL 스킴(카카오맵으로 앱 이동)

### 입양자

- share_token URL로 로그인 없이 현황 조회
- 체크포인트 기반 위치 마커
- 구간별 인계 완료 타임라인
- 현재 담당 봉사자 구간 정보

### LLM / 자동화

- 자정 배치 매칭 시 인계 거점 자동 추천
  (휴게소·기차역·버스터미널·지자체 보호소, 공공데이터포털 수집 → PostGIS waypoints 테이블) - 매칭 확정 알림에 인계 장소명 자동 포함 - SOS·backup 소진 시 현재 위치 기준 인근 보호소 자동 안내
- 자연어 알림 메시지 자동 생성 **(Post-MVP — MVP는 템플릿 메시지 사용)**
- 이상 감지 (핑 미응답, 체크포인트 지연, SOS)
- 긴급 재매칭 (backup_candidates → 인근 봉사자 → 관리자 이메일 알림)
- 협력 보호소 연계 안내 **(Post-MVP)**
- 노쇼 페널티 자동 처리 (30일 정지 자동 적용, 관리자 개입 불필요)

### 부가 페이지

- 문의하기 (보호소 연락처, tel: 링크, 푸터 이메일)
- Admin 페이지
  - 보호소 승인 목록 (대기 중 보호소 승인/거절)
  - 사용자 관리 (검색 + 정지/해제)
  - SOS 수동 개입은 이메일 알림만 수신, 별도 UI 없음

---

## 11. 인증 및 보안

### JWT 전략

- Access Token: 만료 시간 15분
- Refresh Token: 만료 시간 7일, Redis에 저장 (로그아웃·계정 정지 시 즉시 폐기)
- 계정 정지(suspended/banned) 처리 시 Refresh Token 즉시 무효화 → 재로그인 불가

### 보호소 인증

- 사업자등록번호 + 이메일 인증
- 관리자 수동 승인 (`/admin/shelters/{id}/approve`)

### share_token

- UUID v4, 로그인 없이 조회 가능 (읽기 전용)
- 공개 필드 화이트리스트 (봉사자 실명·연락처 비공개):
  - 체크포인트 위치 (위도/경도)
  - 구간별 인계 완료 타임라인
  - 현재 담당 구간 정보 (예: "2구간 이동 중")

**만료 및 데이터 처리 (배치 스케줄러)**

- 이송 완료 또는 취소 후 30일 경과 시 share_token 만료
- 만료 시 FastAPI 배치 스케줄러가 자동 실행:
  1. `checkpoints` 테이블의 위도/경도 → 시/군/구 단위로 비식별화 (정밀 좌표 삭제)
  2. `relay_segments`의 `handover_code` 컬럼 null 처리
  3. `transport_posts`의 `share_token` null 처리
- 봉사 내역(거리, 날짜)은 비식별화 후에도 봉사자 통계용으로 보존

### 인계 확인 (6자리 코드)

**폴백 1: 6자리 코드 수동 입력**

- 인계 코드 입력 시도: IP당 분당 10회 + 계정(user_id)당 분당 5회 제한 (rate limit)

**폴백 2: 인계 완료 요청/승인 (앱 문제 시 최후 수단)**

- 앞 구간 봉사자가 [인계 완료 요청] 버튼 클릭
- 뒷 구간 봉사자에게 인앱 알림 + 이메일 발송: "인계 확인 요청이 왔습니다. 승인하시겠습니까?"
- 뒷 구간 봉사자가 [승인] 클릭 시 → 코드 쌍방 입력과 동일하게 인계 확정 처리
- GPS·카메라 없이 두 사람의 합의만으로 프로세스 진행 가능
- `relay_segments`에 `handover_method (code | qr | manual_approval)` 컬럼으로 인계 방식 기록

**공통**

- 쌍방 확인 완료(handover_code_given_at + received_at 모두 기록) 시 인계 확정
- 한쪽만 확인 후 30분 경과 시 → `needs_verification` 상태로 전환 (자동 노쇼 처리 금지)
- 인계 완료 시 코드 즉시 무효화 (DB 컬럼 비교)

### 챗봇 엔드포인트

- `/chatbot/message`: JWT 인증 필수 (봉사자 role만 허용)

### 노쇼 페널티

- 30일 정지 자동 적용 (관리자 개입 불필요)

---

> 챗봇 인터페이스 상세 명세는 `api-spec.md` Section 9 참고.
