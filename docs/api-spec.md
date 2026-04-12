# API 명세서 (확정본)

> 1주차 인터페이스 합의 결과물. 이후 변경 시 반드시 사전 공지 필요.
> BE = Backend / FE = Frontend / AI = AI 담당자

---

## 공통 규칙

### 인증
- Access Token: httpOnly 쿠키 (만료 15분)
- Refresh Token: httpOnly 쿠키 (만료 7일, Secure, SameSite=Strict)
- 모든 요청에 쿠키 자동 포함. Authorization 헤더 불필요.
- 401 수신 시 FE가 자동으로 `/auth/refresh` 호출 (인터셉터)

### 에러 응답 형식
```json
{ "error": "ERROR_CODE" }
```

### 페이지네이션
- offset 기반: `?page=1&limit=20`
- Response: `{ data: [...], total, page, limit }`

---

## 1. Auth

### POST `/auth/signup/volunteer`
봉사자 회원가입

```json
Request:
{
  "email": "test@gmail.com",
  "password": "abc123!",
  "name": "홍길동",
  "activity_regions": ["서울특별시", "경기도"]
}

Response 200:
{
  "user": { "id": 1, "email": "test@gmail.com", "role": "volunteer" }
}
```

| 에러 코드 | 조건 |
|----------|------|
| `EMAIL_ALREADY_EXISTS` | 이미 가입된 이메일 |
| `WEAK_PASSWORD` | 비밀번호 형식 미충족 |

---

### POST `/auth/signup/shelter`
보호소 회원가입

```json
Request:
{
  "email": "shelter@gmail.com",
  "password": "abc123!",
  "name": "행복보호소",
  "phone": "062-000-0000",
  "contact_email": "contact@shelter.com",
  "address": "광주광역시 서구 OO로 1",
  "shelter_registration_doc_url": "https://s3.../doc.pdf"
}

Response 200:
{
  "user": { "id": 2, "email": "shelter@gmail.com", "role": "shelter" }
}
```

> `contact_email`: 알림 수신용 이메일 (로그인 email과 별도).
> `shelter_registration_doc_url`: nullable. 가입 시 미첨부 가능, 이후 별도 업로드.
> 가입 후 관리자 승인 전까지 대시보드 접근 제한.

| 에러 코드 | 조건 |
|----------|------|
| `EMAIL_ALREADY_EXISTS` | 이미 가입된 이메일 |

---

### POST `/auth/login`

```json
Request:  { "email": "test@gmail.com", "password": "abc123!" }
Response: { "user": { "id": 1, "email": "test@gmail.com", "role": "volunteer" } }
```

> Access Token, Refresh Token은 httpOnly 쿠키로 Set-Cookie.

| 에러 코드 | 조건 |
|----------|------|
| `INVALID_CREDENTIALS` | 이메일/비밀번호 불일치 |
| `ACCOUNT_SUSPENDED` | 계정 정지 상태 |
| `EMAIL_NOT_VERIFIED` | 이메일 미인증 |

---

### POST `/auth/logout`
인증 필요.

```json
Response: { "ok": true }
```

> BE: Refresh Token 즉시 폐기. 쿠키 만료 처리.

---

### POST `/auth/refresh`
인증 필요.

```json
Response: { "ok": true }
```

> BE: 새 Access Token을 Set-Cookie로 내려줌.

| 에러 코드 | 조건 |
|----------|------|
| `REFRESH_TOKEN_EXPIRED` | Refresh Token 만료. FE: /login으로 이동 |

---

### POST `/auth/verify-email/{token}`
인증 불필요.

> BE: 처리 완료 후 302 리다이렉트.
> - 성공: `/login?verified=true`
> - 실패: `/login?error=INVALID_TOKEN`
>
> FE: 쿼리파라미터 보고 토스트 메시지 표시.

---

## 2. 공고 (Transport Posts)

### GET `/posts`
인증 불필요.

```
Query: ?region=광주&date=2026-04-10&animal_size=small&page=1&limit=20

Response 200:
{
  "posts": [
    {
      "id": 1,
      "origin": "광주광역시",
      "destination": "서울특별시",
      "scheduled_date": "2026-04-10",
      "animal_size": "small",
      "status": "recruiting",
      "animal_photo_url": "https://s3.../dog.jpg"
    }
  ],
  "total": 42,
  "page": 1,
  "limit": 20
}
```

---

### POST `/posts`
보호소 인증 필요.

```json
Request:
{
  "origin": "광주광역시",
  "destination": "서울특별시",
  "scheduled_date": "2026-04-10",
  "animal_info": {
    "name": "초코",
    "size": "small",
    "photo_url": "https://s3.../dog.jpg",
    "notes": "겁이 많아요"
  }
}

Response 200:
{
  "id": 1,
  "share_token": "550e8400-e29b-41d4-a716",
  "status": "recruiting"
}
```

> FE: share_token으로 공유 링크 조합.
> `https://{도메인}/public/{share_token}`
> 클립보드 복사 버튼은 FE에서 처리.

---

### GET `/posts/{id}`
인증 불필요.

```json
Response 200:
{
  "id": 1,
  "origin": "광주광역시",
  "destination": "서울특별시",
  "scheduled_date": "2026-04-10",
  "status": "recruiting",
  "animal_info": { "name": "초코", "size": "small", "photo_url": "...", "notes": "..." }
}
```

---

### DELETE `/posts/{id}`
보호소 인증 필요. 본인 공고만 삭제 가능.

```json
Response 200: { "ok": true }
```

| 에러 코드 | 조건 |
|----------|------|
| `POST_NOT_FOUND` | 존재하지 않는 공고 |
| `UNAUTHORIZED` | 본인 공고 아님 |
| `POST_ALREADY_MATCHED` | 매칭 확정된 공고 (삭제 불가) |

---

### PUT `/posts/{id}`
보호소 인증 필요. 본인 공고만 수정 가능.

```json
Request: (변경할 필드만 포함)
{
  "scheduled_date": "2026-04-11",
  "animal_info": { "notes": "수정된 내용" }
}

Response 200: { "ok": true }
```

---

### GET `/posts/upload-url`
보호소 인증 필요.

```
Query: ?filename=dog.jpg

Response 200:
{
  "upload_url": "https://s3.amazonaws.com/...?X-Amz-Signature=...",
  "photo_url": "https://s3.../dog.jpg"
}
```

> S3 Presigned URL 방식.
> FE 흐름: upload_url로 S3에 직접 PUT → photo_url을 POST /posts에 포함.

---

### GET `/posts/public/{share_token}`
인증 불필요.

```json
Response 200:
{
  "animal_info": { "name": "초코", "size": "small", "photo_url": "..." },
  "origin": "광주광역시",
  "destination": "서울특별시",
  "scheduled_date": "2026-04-10",
  "current_segment": { "order": 2, "status": "in_progress" },
  "checkpoints": [
    { "latitude": 35.16, "longitude": 126.85, "recorded_at": "2026-04-10T09:00:00Z" }
  ],
  "timeline": [
    { "segment_order": 1, "completed_at": "2026-04-10T11:00:00Z" }
  ]
}
```

> 봉사자 실명·연락처 비공개.
> FE: 실시간 업데이트는 WebSocket으로.
> WebSocket 연결: `ws://api/ws?share_token=xxxx` (인증 없이 share_token으로 채널 구독)

---

## 3. 봉사자

### POST `/volunteers/schedules`
봉사자 인증 필요.

```json
Request:
{
  "post_id": 5,
  "route_description": "광주 → 천안",
  "origin": "광주광역시 서구",
  "destination": "충남 천안시 서북구",
  "available_date": "2026-04-10",
  "vehicle_available": true,
  "max_animal_size": "medium"
}

Response 200:
{
  "schedule_id": 17,
  "status": "available"
}
```

> `post_id`: nullable. 게시판 진입 시 포함, 챗봇 직접 진입 시 null.
> BE: origin/destination 텍스트 수신 후 Geocoding → geometry 저장.

| 에러 코드 | 조건 |
|----------|------|
| `GEOCODING_FAILED` | 주소 좌표 변환 실패 |

---

### GET `/volunteers/history`
봉사자 인증 필요.

```json
Response 200:
{
  "history": [
    {
      "segment_id": 1,
      "origin": "광주광역시",
      "destination": "천안시",
      "completed_at": "2026-04-10T15:00:00Z",
      "distance_km": 170
    }
  ],
  "total_distance_km": 340
}
```

---

## 4. 매칭

### PATCH `/matching/relay-chains/{chain_id}/approve`
보호소 인증 필요.

```json
Response 200: { "ok": true }
```

> 매칭 플로우: 보호소 승인 → 봉사자 수락(24시간) → 매칭 확정.

| 에러 코드 | 조건 |
|----------|------|
| `CHAIN_NOT_FOUND` | 존재하지 않는 체인 |
| `CHAIN_ALREADY_APPROVED` | 이미 승인된 체인 |
| `CHAIN_EXPIRED` | 24시간 초과 |
| `UNAUTHORIZED` | 본인 공고의 체인이 아님 |

---

### PATCH `/matching/relay-chains/{chain_id}/reject`
보호소 인증 필요.

```json
Response 200: { "ok": true }
```

> 거절 시 해당 `transport_post`의 status가 `recruiting`으로 복귀 → 다음 자정 배치 재처리 대상.

| 에러 코드 | 조건 |
|----------|------|
| `CHAIN_NOT_FOUND` | 존재하지 않는 체인 |
| `CHAIN_ALREADY_APPROVED` | 이미 승인된 체인 |
| `UNAUTHORIZED` | 본인 공고의 체인이 아님 |

---

### POST `/matching/accept/{segment_id}`
봉사자 인증 필요.

```json
Response 200:
{
  "segment": {
    "order": 1,
    "pickup_location": { "name": "광주역", "address": "광주광역시 ..." },
    "dropoff_location": { "name": "천안역", "address": "충남 천안시 ..." },
    "scheduled_time": "2026-04-10T09:00:00Z",
    "handover_code": null,
    "partner": { "name": "김봉사", "phone": "010-1234-5678" },
    "kakao_openchat_url": "https://open.kakao.com/...",
    "waypoints": {
      "train": [{ "name": "천안역", "address": "..." }],
      "bus": [{ "name": "천안터미널", "address": "..." }],
      "rest_area": [{ "name": "천안휴게소", "address": "..." }]
    }
  }
}
```

> `handover_code`: 출발 당일 00:00 이전에는 null.
> 당일 코드 조회: `GET /matching/segments/{segment_id}` 사용.
> waypoints 최대 20개, type별 그룹핑.

---

### POST `/matching/decline/{segment_id}`
봉사자 인증 필요.

```json
Request:  { "reason": "일정 변경" }
Response: { "status": "declined" }
```

---

### GET `/matching/segments/{segment_id}`
봉사자 인증 필요.

```json
Response 200:
{
  "segment": {
    "order": 1,
    "pickup_location": { ... },
    "dropoff_location": { ... },
    "scheduled_time": "...",
    "handover_code": "A3F9K2",
    "partner": { "name": "김봉사", "phone": "010-1234-5678" },
    "kakao_openchat_url": "...",
    "status": "accepted"
  }
}
```

> `handover_code`: 출발 당일 00:00부터 값 포함. 이전에는 null.

---

## 5. 릴레이 트래킹

### POST `/relay/checkpoint`
봉사자 인증 필요.

```json
Request:
{
  "segment_id": 1,
  "type": "departure",
  "latitude": 35.16,
  "longitude": 126.85
}

Response 200:
{
  "checkpoint_id": 10,
  "recorded_at": "2026-04-10T09:00:00Z"
}
```

> `latitude`, `longitude`: nullable. GPS 권한 거부 시 null 허용.
> FE: GPS 거부 시 "위치 정보 없이 기록됩니다" 안내 후 전송.

---

### POST `/relay/handover/verify`
봉사자 인증 필요.

```json
Request:  { "segment_id": 1, "code": "A3F9K2" }

Response 200:
{
  "status": "completed" | "waiting_partner"
}
```

> `waiting_partner`: 상대방 미입력 상태. 상대방 입력 완료 시 Web Push 발송.
> FE: waiting_partner 화면 표시 후 폴링 불필요 (Web Push로 완료 알림 수신).

| 에러 코드 | 조건 |
|----------|------|
| `INVALID_CODE` | 코드 불일치 |
| `RATE_LIMIT_EXCEEDED` | IP당 분당 10회 또는 계정당 분당 5회 초과 |

---

### POST `/relay/handover/request/{segment_id}`
봉사자 인증 필요. (폴백: 코드 입력 불가 시)

```json
Response 200: { "ok": true }
```

> 뒷 구간 봉사자에게 인앱 알림 + 이메일 발송.

---

### POST `/relay/handover/approve/{segment_id}`
봉사자 인증 필요. (폴백: 인계 완료 요청 수락)

```json
Response 200: { "status": "completed" }
```

---

### PATCH `/relay/segments/{id}/handover-location`
봉사자 인증 필요. **앞 구간 봉사자만 가능.**

```json
Request:  { "waypoint_id": 5 }
Response: { "dropoff_location": { "name": "천안터미널", "address": "..." } }
```

> 변경 시 상대 봉사자에게 Web Push 자동 발송.

| 에러 코드 | 조건 |
|----------|------|
| `UNAUTHORIZED_SEGMENT` | 뒷 구간 봉사자가 요청 시 |

---

### POST `/relay/emergency/sos`
봉사자 인증 필요.

```json
Request:
{
  "segment_id": 1,
  "latitude": 36.35,
  "longitude": 127.38
}

Response 200:
{
  "message": "긴급 재매칭 요청이 접수되었습니다."
}
```

> FE: 실수 클릭 방지용 확인 다이얼로그 표시 후 전송.

---

### POST `/relay/emergency/delay`
봉사자 인증 필요.

```json
Request:  { "segment_id": 1, "message": "교통 체증으로 30분 지연 예상" }
Response: { "ok": true }
```

> 다음 구간 봉사자 + 보호소에 Web Push/WebSocket 발송.

---

## 6. 알림

### GET `/notifications/unread`
인증 필요.

```json
Response 200:
{
  "notifications": [
    {
      "id": 1,
      "type": "matching_proposed",
      "message": "새로운 매칭 제안이 도착했어요.",
      "payload": { "segment_id": 42, "url": "/volunteer/matching/42" },
      "created_at": "2026-04-10T09:00:00Z"
    }
  ]
}
```

> WebSocket 재연결 시 FE가 호출하는 폴링 폴백 API.

**notification type 전체 목록**

| type | 설명 |
|------|------|
| `matching_proposed` | 매칭 제안 |
| `matching_confirmed` | 매칭 확정 |
| `ping_check` | 핑 체크 (출발 확인 요청) |
| `ping_no_response` | 핑 미응답 경고 (보호소용) |
| `delay_reported` | 지연 신고 알림 |
| `sos_triggered` | SOS 발생 |
| `handover_waiting_confirm` | 인계 코드 대기 |
| `handover_location_changed` | 인계 장소 변경 |
| `matching_failed` | 배치 실패 알림 (보호소용) |

---

### PATCH `/notifications/{id}/read`
인증 필요.

```json
Response 200: { "ok": true }
```

---

### GET `/notifications/push/vapid-key`
인증 불필요.

```json
Response 200: { "public_key": "BNxx..." }
```

> FE: 앱 초기 로딩 시 1회 호출 후 캐싱.

---

### POST `/notifications/push/subscribe`
봉사자 인증 필요.

```json
Request:
{
  "endpoint": "https://fcm.googleapis.com/...",
  "keys": { "p256dh": "...", "auth": "..." }
}

Response 200: { "ok": true }
```

---

### DELETE `/notifications/push/subscribe`
봉사자 인증 필요.

```json
Response 200: { "ok": true }
```

---

## 7. 보호소 대시보드

### GET `/shelter/me`
보호소 인증 필요.

```json
Response 200:
{
  "id": 1,
  "name": "행복 동물 보호소",
  "email": "shelter@example.com",
  "verified_at": "2026-04-01T00:00:00Z"
}
```

---

### GET `/shelter/dashboard`
보호소 인증 필요.

```json
Response 200:
{
  "posts": [
    {
      "id": 1,
      "origin": "광주광역시",
      "destination": "서울특별시",
      "scheduled_date": "2026-04-10",
      "status": "recruiting",
      "volunteer_count": 2
    }
  ]
}
```

---

### GET `/shelter/posts/{id}/relay`
보호소 인증 필요.

```json
Response 200:
{
  "segments": [
    {
      "order": 1,
      "volunteer_name": "홍길동",
      "pickup_location": { "name": "광주역", "address": "..." },
      "dropoff_location": { "name": "천안역", "address": "..." },
      "status": "in_progress",
      "ping_status": "confirmed" | "no_response" | "pending"
    }
  ]
}
```

> FE: WebSocket `ping.confirmed` / `ping.no_response` 이벤트 수신 시
> ping_status 실시간 갱신.
> `no_response` → 주황색 경고 표시.
> 봉사자 뒤늦게 응답 시 `confirmed`로 전환.

---

## 8. Admin

### GET `/admin/shelters/pending`
Admin 인증 필요.

```json
Response 200:
{
  "shelters": [
    {
      "id": 1,
      "name": "행복보호소",
      "email": "shelter@gmail.com",
      "shelter_registration_doc_url": "https://s3.../doc.pdf",
      "created_at": "2026-04-01T09:00:00Z"
    }
  ]
}
```

---

### POST `/admin/shelters/{id}/approve`
Admin 인증 필요.

```json
Response 200: { "ok": true }
```

---

### POST `/admin/shelters/{id}/reject`
Admin 인증 필요.

```json
Request:  { "reason": "서류 미비" }
Response: { "ok": true }
```

---

### GET `/admin/users`
Admin 인증 필요.

```
Query: ?email=test@gmail.com&name=홍길동&page=1&limit=20

Response 200:
{
  "users": [
    {
      "id": 1,
      "email": "test@gmail.com",
      "name": "홍길동",
      "role": "volunteer",
      "account_status": "active"
    }
  ],
  "total": 1
}
```

---

### POST `/admin/users/{id}/suspend`
Admin 인증 필요.

```json
Request:  { "reason": "노쇼 3회" }
Response: { "ok": true }
```

> BE: Refresh Token 즉시 무효화 → 재로그인 불가.

---

### POST `/admin/users/{id}/unsuspend`
Admin 인증 필요.

```json
Response: { "ok": true }
```

---

## 9. 챗봇

### POST `/chatbot/message`
봉사자 인증 필요.

```json
Request:
{
  "session_id": null,
  "post_id": 5,
  "message": null
}

Response 200:
{
  "session_id": "550e8400-e29b-41d4-a716",
  "state": "ASK_ORIGIN",
  "message": "어느 지역에서 출발하실 수 있나요?",
  "input_type": "address_search" | "date_picker" | "buttons" | null,
  "options": ["있어요", "없어요"],
  "auto_filled": {
    "available_date": "2026-04-10",
    "max_animal_size": "small",
    "post_origin": "광주광역시",
    "post_destination": "서울특별시"
  },
  "completed": false,
  "schedule_id": null
}
```

**state 전체 목록**

| state | input_type | options |
|-------|-----------|---------|
| `ASK_ORIGIN` | `address_search` | null |
| `ASK_DESTINATION` | `address_search` | null |
| `ASK_DATE` | `date_picker` | null |
| `ASK_VEHICLE` | `buttons` | `["있어요", "없어요"]` |
| `ASK_ANIMAL_SIZE` | `buttons` | `["소형 (5kg 이하)", "중형 (5~15kg)", "대형 (15kg 이상)"]` |
| `CONFIRM` | `buttons` | `["등록하기", "처음부터 다시"]` |
| `COMPLETED` | `null` | null |

**post_id에 따른 state SKIP**

| post_id | SKIP되는 state |
|---------|--------------|
| 있음 | `ASK_DATE`, `ASK_ANIMAL_SIZE` |
| 없음 | SKIP 없음 |

**FE 렌더링 규칙**
- `address_search`: 카카오 주소 검색 모달. 텍스트 직접 입력 불가.
- `date_picker`: 달력 위젯. 오늘 이후 자유 선택. ISO 형식(`2026-04-10`)으로 전송.
- `buttons`: options 배열 버튼 렌더링. 텍스트 입력창 숨김.
- `null`: 입력 UI 없음 (COMPLETED).
- `auto_filled` 항목: CONFIRM 화면에서 회색 표시 (수정 불가).
- `auto_filled` 있을 때: 챗봇 상단에 공고 요약 카드 고정 표시.

**에러 코드**

| 에러 코드 | 조건 | 처리 |
|----------|------|------|
| `GEOCODING_FAILED` | 주소 좌표 변환 실패 | ASK_ORIGIN 복귀 |
| `INVALID_INPUT` | 버튼 state에서 예상 외 입력 | 현재 state 유지 |
| `SCHEDULE_SAVE_FAILED` | volunteer_schedules 저장 실패 | CONFIRM 복귀 |
| `SESSION_EXPIRED` | 세션 1시간 초과 | FE: 세션 초기화 후 재시작 |

> `session_id`: 첫 요청 시 null → BE가 생성해서 반환. 이후 요청부터 포함.
> `completed: true` 시 BE 내부에서 volunteer_schedules 저장까지 처리. FE 별도 호출 불필요.
> `session_id` 저장: FE는 sessionStorage 사용.

---

### GET `/chatbot/session/{session_id}`
봉사자 인증 필요.

```json
Response 200:
{
  "state": "ASK_VEHICLE",
  "message": "차량이 있으신가요?",
  "input_type": "buttons",
  "options": ["있어요", "없어요"],
  "auto_filled": { ... }
}
```

> FE 새로고침 시 sessionStorage의 session_id로 마지막 state 복원.

| 에러 코드 | 조건 |
|----------|------|
| `SESSION_EXPIRED` | 세션 만료 또는 존재하지 않음 |

---

### DELETE `/chatbot/session/{session_id}`
봉사자 인증 필요.

```json
Response 200: { "ok": true }
```

---

## 10. WebSocket 이벤트

### 연결
```
ws://api/ws                        (로그인 사용자, 쿠키 인증)
ws://api/ws?share_token=xxxx       (입양자 조회 페이지, 인증 없음)
```

> 재연결 시 `GET /notifications/unread` 호출로 밀린 알림 수신.

### 이벤트 포맷
```json
{
  "event": "이벤트명",
  "payload": { ... }
}
```

### 이벤트 목록

| event | 수신자 | payload |
|-------|--------|---------|
| `checkpoint.updated` | 입양자 조회 페이지 | `{ transport_post_id, segment_order, latitude, longitude, recorded_at }` |
| `ping.confirmed` | 보호소 대시보드 | `{ segment_id, volunteer_name }` |
| `ping.no_response` | 보호소 대시보드 | `{ segment_id, volunteer_name, scheduled_time }` |
| `delay.reported` | 보호소 대시보드 | `{ segment_id, message }` |
| `sos.triggered` | 보호소 대시보드 | `{ segment_id, latitude, longitude }` |

---

## 11. Web Push payload 포맷

```json
{
  "type": "notification type",
  "message": "알림 메시지",
  "segment_id": 42,
  "url": "/volunteer/matching/42"
}
```

> FE: 알림 클릭 시 `url` 경로로 이동.
> PWA 미설치(iOS) 또는 Push 권한 거부 시 이메일 자동 대체 발송.
