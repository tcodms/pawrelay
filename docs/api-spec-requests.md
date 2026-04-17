# API 스펙 추가 요청 목록

> 프론트엔드 구현 중 `api-spec.md`에 없는 엔드포인트가 필요한 것들을 정리합니다.
> 백엔드 담당자와 협의 후 `api-spec.md`에 반영해 주세요.

---

## 1. 보호소 프로필 조회

**요청:** `GET /shelters/me`

**필요 이유:**
보호소 대시보드 헤더에 보호소 이름을 표시해야 합니다. 현재 하드코딩된 더미값 사용 중.

**예상 응답:**
```json
{
  "id": 1,
  "name": "행복 동물 보호소",
  "email": "shelter@example.com",
  "verified_at": "2026-04-01T00:00:00Z"
}
```

**관련 파일:** `frontend/lib/api/shelter.ts`

---

## 2. 보호소 측 매칭 승인

**요청:** `PATCH /relay-chains/{chain_id}/approve`

**필요 이유:**
LLM이 생성한 릴레이 체인을 보호소가 최종 승인하는 기능.
CLAUDE.md 매칭 플로우: "보호소 확인(24시간) → 봉사자 수락(24시간) → 매칭 확정"

**예상 요청/응답:**
```json
// Request: body 없음
// Response 200:
{ "ok": true }
```

**에러 케이스 필요:**
| 에러 코드 | 조건 |
|----------|------|
| `CHAIN_ALREADY_APPROVED` | 이미 승인된 체인 |
| `CHAIN_EXPIRED` | 24시간 초과 |

**관련 파일:** `frontend/lib/api/matching.ts`, `frontend/app/dashboard/page.tsx`

---

## 3. 보호소 측 매칭 거절 / 재매칭 요청

**요청:** `PATCH /relay-chains/{chain_id}/reject`

**필요 이유:**
보호소가 LLM 매칭 결과가 마음에 들지 않을 때 재매칭을 요청하는 기능.
거절 시 해당 공고는 다음 자정 배치에서 재처리되어야 합니다.

**예상 요청/응답:**
```json
// Request: body 없음 (또는 거절 사유 선택지 있으면 추가 논의)
// Response 200:
{ "ok": true }
```

**관련 파일:** `frontend/lib/api/matching.ts`, `frontend/app/dashboard/page.tsx`

---

## 4. 공고 삭제

**요청:** `DELETE /posts/{id}`

**필요 이유:**
공고 상세 페이지에 삭제 버튼이 있습니다. 현재 백엔드 연동 전으로 버튼 클릭 시 안내 메시지만 표시.

**예상 응답:**
```json
// Response 200:
{ "ok": true }
```

**에러 케이스 필요:**
| 에러 코드 | 조건 |
|----------|------|
| `POST_NOT_FOUND` | 존재하지 않는 공고 |
| `UNAUTHORIZED` | 본인 공고 아님 |
| `POST_ALREADY_MATCHED` | 이미 매칭 확정된 공고 (삭제 불가 여부 결정 필요) |

**관련 파일:** `frontend/lib/api/posts.ts`, `frontend/app/dashboard/posts/[id]/page.tsx`

---

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

## 참고

- 5·6·7·8번은 새 엔드포인트가 아닌 **기존 응답 필드 확장** 요청입니다. 백엔드 쿼리 수정만으로 처리 가능합니다.
- 위 항목들은 `frontend/lib/api/` 하위 파일에 TODO 주석으로 표시되어 있습니다.
- 엔드포인트 확정 시 해당 파일의 TODO를 해제하면 바로 연동 가능합니다.
