# API 스펙 추가 요청 목록

> 프론트엔드 구현 중 `api-spec.md`에 없는 엔드포인트가 필요한 것들을 정리합니다.
> 백엔드 담당자와 협의 후 `api-spec.md`에 반영해 주세요.

---

## 1. 보호소 프로필 조회

> **✅ api-spec.md에 반영 완료** — `GET /shelter/me` (단수)
> FE에서 경로를 `/shelter/me`로 맞출 것.

**관련 파일:** `frontend/lib/api/shelter.ts`

---

## 2. 보호소 측 매칭 승인

> **✅ api-spec.md에 반영 완료** — `PATCH /matching/relay-chains/{chain_id}/approve`
> FE에서 경로에 `/matching/` prefix 추가할 것.

**관련 파일:** `frontend/lib/api/matching.ts`, `frontend/app/dashboard/page.tsx`

---

## 3. 보호소 측 매칭 거절 / 재매칭 요청

> **✅ api-spec.md에 반영 완료** — `PATCH /matching/relay-chains/{chain_id}/reject`
> FE에서 경로에 `/matching/` prefix 추가할 것.

**관련 파일:** `frontend/lib/api/matching.ts`, `frontend/app/dashboard/page.tsx`

---

## 4. 공고 삭제

> **✅ api-spec.md에 반영 완료** — `DELETE /posts/{id}`

**관련 파일:** `frontend/lib/api/posts.ts`, `frontend/app/dashboard/posts/[id]/page.tsx`

---

## 5. `GET /shelter/dashboard` 응답에 `animal_info` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
보호소 대시보드 공고 카드에서 동물 이름, 크기, 사진을 표시해야 합니다.
현재 `GET /shelter/dashboard` 응답에는 해당 필드가 없어 실 API 전환 시 카드 UI가 깨집니다.

**현재 응답 (스펙):**
```json
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

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "origin": "광주광역시",
      "destination": "서울특별시",
      "scheduled_date": "2026-04-10",
      "status": "recruiting",
      "volunteer_count": 2,
      "animal_info": {
        "name": "초코",
        "size": "small",
        "photo_url": "https://s3.../dog.jpg"
      }
    }
  ]
}
```

**관련 파일:** `frontend/app/dashboard/page.tsx`, `frontend/lib/dummy-posts.ts`

---

## 6. `GET /shelter/dashboard` 응답에 `chain_id` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
`status: "waiting"` 공고에서 보호소가 LLM 매칭 결과를 승인/거절할 때
`PATCH /matching/relay-chains/{chain_id}/approve|reject`를 호출해야 합니다.
그런데 현재 대시보드 응답에 `chain_id`가 없어서 승인/거절 요청 시 올바른 체인을 특정할 수 없습니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "status": "waiting",
      "chain_id": 101,
      "..."
    }
  ]
}
```

> `chain_id`는 `status: "waiting"`인 공고에만 포함. 다른 상태에서는 `null` 또는 필드 생략.

**관련 파일:** `frontend/app/dashboard/page.tsx`, `frontend/lib/api/matching.ts`

---

## 7. `GET /shelter/dashboard` 응답에 `share_token` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
`status: "in_progress"` 공고 카드의 "봉사 현황 보기" 버튼이 `/track/{share_token}` 링크로 이동합니다.
현재 응답에 `share_token`이 없어 링크 생성이 불가합니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 7,
      "status": "in_progress",
      "share_token": "550e8400-e29b-41d4-a716",
      "..."
    }
  ]
}
```

> `share_token`은 `status: "in_progress"` 또는 `"completed"` 공고에만 포함. 그 외 상태는 `null`.

**관련 파일:** `frontend/app/dashboard/page.tsx`

---

## 8. `GET /posts/{id}` 응답에 `volunteers` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
공고 상세 페이지(보호소·봉사자 모두)에서 "현재 지원 N명"을 표시해야 합니다.
현재 스펙에는 지원자 정보가 없어 실 API 전환 시 해당 UI가 깨집니다.

**현재 응답 (스펙):**
```json
{
  "id": 1,
  "origin": "광주광역시",
  "destination": "서울특별시",
  "scheduled_date": "2026-04-10",
  "status": "recruiting",
  "animal_info": { "name": "초코", "size": "small", "photo_url": "...", "notes": "..." }
}
```

**요청 응답 (추가 필요 필드):**
```json
{
  "id": 1,
  "origin": "광주광역시",
  "destination": "서울특별시",
  "scheduled_date": "2026-04-10",
  "status": "recruiting",
  "animal_info": { "name": "초코", "size": "small", "photo_url": "...", "notes": "..." },
  "volunteers": [
    { "id": 1, "name": "김봉사", "from": "광주역", "to": "천안역" }
  ]
}
```

> **역할별 응답 필터링 필수 (백엔드 강제 적용):**
>
> - `role: shelter` — 전체 `volunteers` 배열 반환 (이름, 구간 포함)
> - `role: volunteer` — `volunteers` 배열 대신 `volunteer_count`(숫자)만 반환
>
> 예시 응답:
> ```json
> // shelter role
> { "volunteers": [{ "id": 1, "name": "김봉사", "from": "광주역", "to": "천안역" }] }
>
> // volunteer role
> { "volunteer_count": 1 }
> ```
>
> 봉사자 실명·연락처는 매칭 확정 후 해당 봉사자에게만 공개. 공고 상세에서는 노출 금지.

**관련 파일:** `frontend/app/dashboard/posts/[id]/page.tsx`, `frontend/app/volunteer/posts/[id]/page.tsx`

---

## 9. 챗봇 방식 변경 (자연어 LLM 파이프라인)

> **✅ api-spec.md 섹션 9 전면 재작성 완료**
>
> 기존 상태 머신(`ASK_ORIGIN`, `ASK_DATE`, `buttons`, `address_search` 위젯 등)을
> **자연어 LLM 파이프라인**으로 전환.
>
> - FE: 항상 자유 입력 textarea. 별도 위젯/모달 없음.
> - BE: 대화 기록을 Redis 세션으로 관리. FE는 최신 메시지 1건만 전송.
> - LLM: 자유 발화에서 필수 필드 파싱·정규화 후 `volunteer_schedules` 저장까지 처리.

---

---

## 10. 봉사자 매칭 제안 API에 `notified_at` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
매칭 수락/거절 24시간 기한의 기산점이 "알림 발송 시각"입니다 (design.md 명시).
매칭 생성 시각(`created_at`)이 아닌 알림이 실제로 발송된 시각부터 카운트해야 FE에서 정확한 타이머를 표시할 수 있습니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "segment_id": 42,
  "notified_at": "2026-04-18T00:05:00Z",
  "expires_at": "2026-04-19T00:05:00Z"
}
```

> `expires_at`은 `notified_at + 24시간`으로 BE에서 계산해서 내려주면 FE 구현이 단순해집니다.

**관련 파일:** `frontend/app/volunteer/matching/[segment_id]/page.tsx` (미구현)

---

## 11. 봉사자 매칭 제안 상세 엔드포인트 요청

**요청:** 새 엔드포인트

**필요 이유:**
`/volunteer/matching/{segment_id}` 상세 페이지에서 아래 정보를 한 번에 조회해야 합니다.

**요청 응답:**
```json
{
  "segment_id": 42,
  "status": "proposed",
  "notified_at": "2026-04-18T00:05:00Z",
  "expires_at":  "2026-04-19T00:05:00Z",
  "my_segment": { "from": "광주광역시 북구", "to": "천안역", "scheduled_time": "09:00" },
  "matching_reason": "출발지가 공고 출발지와 일치하고...",
  "chain": [
    { "order": 1, "from": "광주광역시 북구", "to": "천안역", "is_me": true },
    { "order": 2, "from": "천안역", "to": "수원역" },
    { "order": 3, "from": "수원역", "to": "서울 강남구" }
  ],
  "handover_candidates": [
    { "name": "천안아산역", "type": "station",   "distance_km": 0.3 },
    { "name": "천안터미널", "type": "terminal",  "distance_km": 1.2 },
    { "name": "목천휴게소", "type": "rest_area", "distance_km": 8.5 }
  ],
  "animal_info": { "name": "초코", "size": "small", "photo_url": "..." },
  "open_chat_url": "https://open.kakao.com/o/..."
}
```

> `handover_candidates`는 type별로 그룹핑하여 FE에서 기차역 / 휴게소 / 버스터미널 섹션으로 표시합니다.
> 인계 코드는 출발 당일 00:00 이전 `null`, 당일부터 6자리 코드 반환.

**관련 엔드포인트:** `GET /matching/segments/{segment_id}`
**관련 파일:** `frontend/app/volunteer/matching/[segment_id]/page.tsx` (미구현)

---

---

## 12. 알림 payload에 `chat_session_id` 필드 추가 요청

**요청:** `GET /notifications/unread` 및 WebSocket 알림 이벤트 응답 확장

**필요 이유:**
채팅 헤더의 종 모양 알림 목록에서 항목을 탭하면 해당 챗봇 세션으로 딥링크해야 합니다.
알림마다 어느 채팅방으로 이동해야 할지 알 수 없으면 FE에서 라우팅이 불가합니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "id": 1,
  "type": "matching_proposed" | "matching_confirmed" | "handover_reminder",
  "title": "매칭 제안이 도착했어요",
  "body": "초코 릴레이 봉사 구간이 배정됐어요",
  "chat_session_id": "uuid-...",
  "segment_id": 42,
  "is_read": false,
  "created_at": "2026-04-18T00:05:00Z"
}
```

> `chat_session_id`: 알림 탭 시 이동할 챗봇 세션 ID. 해당 세션 채팅방에 매칭 제안/확정 버블이 표시되어 있어야 함.
> `segment_id`: 상세 페이지(`/volunteer/matching/{segment_id}`) 이동용. type이 `matching_proposed` / `matching_confirmed`인 경우에만 포함.

**읽음 처리 엔드포인트 (기존 스펙 확인 요청):**
`PATCH /notifications/{id}/read` 또는 `POST /notifications/read-all` — api-spec.md에 없으면 추가 필요.

**관련 파일:** `frontend/app/volunteer/chat/page.tsx` (종 모양 버튼, 미구현)

---

## 13. `GET /shelter/dashboard` 응답에 `chain_expires_at` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
보호소 매칭 결과 확인 UI에 24시간 승인 기한 카운트다운 및 12시간 리마인더 배지를 표시해야 합니다.
item 6에서 `chain_id`는 요청했지만 타이머 기산점이 없으면 FE에서 기한을 계산할 수 없습니다.
봉사자 측 item 10의 `expires_at`과 동일한 맥락입니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "status": "waiting",
      "chain_id": 101,
      "chain_expires_at": "2026-04-19T00:05:00Z"
    }
  ]
}
```

> `chain_expires_at`은 `status: "waiting"`인 공고에만 포함. 그 외 상태는 `null` 또는 필드 생략.
> BE에서 `chain 생성 시각 + 24시간`으로 계산해서 내려주면 FE 구현이 단순해집니다.

**관련 파일:** `frontend/app/dashboard/page.tsx`

---

## 14. `GET /shelter/dashboard` 응답에 `matching_reason` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
보호소 대시보드의 매칭 결과 바텀시트에서 LLM이 생성한 매칭 이유를 표시해야 합니다.
FE 코드에서 이미 `selectedPost.matchingReason`을 렌더링 중이나 실제 API 응답에 해당 필드가 없습니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "status": "waiting",
      "chain_id": 101,
      "matching_reason": "출발지가 공고 출발지와 일치하고 차량 보유로 소형견 운송에 적합합니다."
    }
  ]
}
```

> `matching_reason`은 `status: "waiting"`인 공고에만 포함. 그 외 상태는 `null` 또는 필드 생략.

**관련 파일:** `frontend/app/dashboard/page.tsx`

---

## 15. Web Push payload에 `chat_session_id` 추가 요청

**요청:** `api-spec.md` 섹션 11 (Web Push payload 포맷) 업데이트

**필요 이유:**
item 12에서 `GET /notifications/unread` 응답에 `chat_session_id`를 요청했지만,
Web Push 알림을 탭했을 때도 챗봇 세션으로 딥링크해야 합니다.
현재 api-spec.md 섹션 11의 payload에는 `chat_session_id`가 없어 푸시 탭 시 라우팅 불가합니다.

**현재 api-spec.md 섹션 11:**
```json
{
  "type": "notification type",
  "message": "알림 메시지",
  "segment_id": 42,
  "url": "/volunteer/matching/42"
}
```

**요청 payload (추가 필요 필드):**
```json
{
  "type": "matching_proposed",
  "message": "매칭 제안이 도착했어요",
  "segment_id": 42,
  "url": "/volunteer/matching/42",
  "chat_session_id": "uuid-..."
}
```

> `chat_session_id`: `matching_proposed` / `matching_confirmed` 타입에만 포함. 그 외 타입은 `null`.

**관련 파일:** `frontend/app/volunteer/chat/page.tsx` (종 모양 버튼, 미구현)

---

## 16. Notification type 이름 통일 확인 요청

**요청:** 확인 및 api-spec.md 수정

**내용:**
아래 두 문서에서 같은 개념의 알림 타입 이름이 다르게 표기되어 있습니다. 어느 쪽으로 확정할지 결정 후 두 문서를 통일해 주세요.

| 문서 | 표기 |
|------|------|
| `api-spec.md` 섹션 6 notification type 목록 | `handover_waiting_confirm` |
| `api-spec-requests.md` item 12 payload 예시 | `handover_reminder` |

> FE에서 `notification.type`을 분기 처리하므로 이름이 확정되어야 구현 가능합니다.

---

## 17. `GET /matching/segments/{segment_id}` 응답 필드 확장 요청

**요청:** 기존 엔드포인트 응답 확장 (item 11의 구조 기반)

**필요 이유:**
봉사자 매칭 상세 페이지(`/volunteer/matching/[segment_id]`)에서 현재 응답에 없는 필드들을 더미값으로 표시 중입니다.
실 API 연동 시 아래 필드가 없으면 동물 정보, 카카오맵, 시간, AI 매칭 이유가 모두 더미로 노출됩니다.

**현재 `SegmentDetail` 응답 (구현된 필드):**
```json
{
  "order": 1,
  "status": "proposed",
  "pickup_location": { "name": "광주광역시 북구", "address": "광주광역시 북구 용봉동" },
  "dropoff_location": { "name": "천안아산역", "address": "충남 아산시 배방읍 장재리" },
  "scheduled_time": "2026-04-10T09:00:00Z",
  "handover_code": null,
  "partner": { "name": "이릴레이", "phone": "010-1234-5678" },
  "kakao_openchat_url": "https://open.kakao.com/o/..."
}
```

**추가 요청 필드:**
```json
{
  "animal_info": {
    "name": "초코",
    "size": "small",
    "photo_url": "https://s3.../dog.jpg"
  },
  "matching_reason": "출발지가 공고 출발지와 일치하고 차량 보유로 소형견 운송에 적합합니다.",
  "depart_time": "09:00",
  "estimated_arrival_time": "10:40",
  "notified_at": "2026-04-19T04:00:00Z",
  "expires_at": "2026-04-20T04:00:00Z",
  "pickup_location": {
    "name": "광주광역시 북구",
    "address": "광주광역시 북구 용봉동",
    "lat": 35.1796,
    "lng": 126.9112
  },
  "dropoff_location": {
    "name": "천안아산역",
    "address": "충남 아산시 배방읍 장재리",
    "lat": 36.7951,
    "lng": 127.1046
  },
  "waypoints": {
    "train": [
      { "name": "천안아산역", "address": "충남 아산시 배방읍 장재리", "distance_km": 0.3, "lat": 36.7951, "lng": 127.1046 }
    ],
    "rest_area": [
      { "name": "목천휴게소", "address": "충남 천안시 동남구 목천읍", "distance_km": 8.5, "lat": 36.7150, "lng": 127.1456 }
    ]
  },
  "kakao_map_url": "https://map.kakao.com/link/from/광주광역시 북구,35.1796,126.9112/to/천안아산역,36.7951,127.1046"
}
```

> `pickup_location`, `dropoff_location`의 `lat`, `lng`는 카카오맵 마커·경로 표시에 필수입니다.
> `waypoints`의 `lat`, `lng`도 마찬가지로 지도 위 인계 후보지 마커 표시에 필요합니다.
> `notified_at` / `expires_at`은 24시간 수락 기한 카운트다운 타이머용입니다 (item 10 참고).
> `depart_time`, `estimated_arrival_time`은 구간 카드 및 채팅 확정 버블에 표시됩니다.

**관련 파일:** `frontend/app/volunteer/matching/[segment_id]/page.tsx`, `frontend/lib/api/matching.ts`

---

## 18. `GET /shelter/dashboard` 응답에 `chain_status` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
자동 승인(`auto_approved`) 상태와 보호소 대기(`pending_shelter`) 상태를 FE에서 구분해야 합니다.
`auto_approved`일 때 카운트다운 대신 "자동 승인됨" 배너와 1시간 취소 버튼을 표시해야 하고, 카드 버튼 레이블도 달라집니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "status": "waiting",
      "chain_id": 101,
      "chain_expires_at": "2026-04-19T00:05:00Z",
      "chain_status": "pending_shelter"
    }
  ]
}
```

> `chain_status` 가능 값: `"pending_shelter"` (보호소 응답 대기) | `"auto_approved"` (24시간 초과 자동 승인)
> `status: "waiting"`인 공고에만 포함. 그 외 상태는 `null`.

**관련 파일:** `frontend/app/dashboard/page.tsx`, `frontend/lib/api/posts.ts`

---

## 19. `GET /shelter/dashboard` 응답에 `relay_segments` 필드 추가 요청

**요청:** 기존 엔드포인트 응답 확장

**필요 이유:**
보호소 매칭 결과 바텀시트에서 릴레이 체인(구간별 봉사자·구간·출발 시각)을 시각화해야 합니다.
현재 `waiting` 상태 공고에 체인 구성 정보가 없어 릴레이 체인이 표시되지 않습니다.

**요청 응답 (추가 필요 필드):**
```json
{
  "posts": [
    {
      "id": 1,
      "status": "waiting",
      "chain_id": 101,
      "relay_segments": [
        {
          "volunteer_name": "김봉사",
          "from_area": "광주역",
          "to_area": "천안역",
          "depart_time": "09:00"
        },
        {
          "volunteer_name": "이릴레이",
          "from_area": "천안역",
          "to_area": "서울 강남구",
          "depart_time": "11:30"
        }
      ]
    }
  ]
}
```

> `relay_segments`는 `status: "waiting"`인 공고에만 포함. 그 외 상태는 `null` 또는 필드 생략.
> `depart_time`은 `HH:MM` 형식의 현지 시각 문자열.

**관련 파일:** `frontend/app/dashboard/page.tsx`, `frontend/lib/api/posts.ts`

---

## 참고

- 1·2·3·4번은 api-spec.md에 이미 반영되어 있습니다. FE에서 경로만 맞추면 바로 연동 가능합니다.
- 5·6·7·8번은 새 엔드포인트가 아닌 **기존 응답 필드 확장** 요청입니다. 백엔드 쿼리 수정만으로 처리 가능합니다.
- 10·11·12번은 매칭 알림 UI 구현 시 필요합니다. 백엔드와 사전 협의 후 진행하세요.
- 13·14·18·19번은 보호소 매칭 승인 UI (타이머·사유·자동승인·릴레이 체인)를 위한 필드 확장입니다. 모두 `GET /shelter/dashboard` 응답 확장이므로 한 번에 처리하면 됩니다.
- 15·16번은 Web Push 딥링크 및 타입명 통일을 위한 확인 요청입니다.
- 17번은 매칭 상세 페이지에서 더미 없이 동작하기 위한 `GET /matching/segments/{segment_id}` 응답 확장 요청입니다. item 11의 구조와 함께 처리하면 됩니다.
- 위 항목들은 `frontend/lib/api/` 하위 파일에 TODO 주석으로 표시되어 있습니다.
- 엔드포인트 확정 시 해당 파일의 TODO를 해제하면 바로 연동 가능합니다.
