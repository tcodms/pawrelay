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

## 참고

- 위 항목들은 `frontend/lib/api/` 하위 파일에 TODO 주석으로 표시되어 있습니다.
- 엔드포인트 확정 시 해당 파일의 TODO를 해제하면 바로 연동 가능합니다.
