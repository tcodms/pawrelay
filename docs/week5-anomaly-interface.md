# Week5 Anomaly Detector Interface

## 개요

- 역할 분리: `BE 감지 -> AI 판정 -> BE 실행`
- AI는 DB 저장이나 REST 실행 없이 `decision payload`만 반환한다.

## 입력 채널

- `pawrelay:sos`
- `pawrelay:needs_verify`
- `pawrelay:checkpoint_delay`
- `pawrelay:backup_exhausted`
- `pawrelay:ping_no_response`
- `pawrelay:pre_departure_no_show`

## 출력 채널

- `pawrelay:ai:decision`

## 지역 정규화 기준

- AI는 입력 지역 문자열을 17개 시/도 공식 명칭으로 정규화한다.
- 예:
  - `충남` -> `충청남도`
  - `서울` -> `서울특별시`
  - `Chungcheongnam-do` -> `충청남도`

## 입력 Payload 예시

### `pawrelay:sos`

```json
{
  "segment_id": 1,
  "volunteer_id": 42,
  "latitude": 36.35,
  "longitude": 127.38,
  "activity_region": "충남"
}
```

예상 결과:
- `decision = shelter_recommend` 또는 `admin_alert`

### `pawrelay:needs_verify`

```json
{
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "volunteer_name": "홍길동",
  "pickup_location": "서울 강남구 역삼동",
  "dropoff_location": "수원역 1번 출구",
  "scheduled_time": "2026-05-07T14:00:00+09:00",
  "handover_code_given_at": "2026-05-07T15:05:00+09:00",
  "handover_code_received_at": null
}
```

예상 결과:
- `decision = no_show_candidate` 또는 `admin_alert`

### `pawrelay:checkpoint_delay`

```json
{
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "volunteer_name": "홍길동",
  "scheduled_time": "2026-05-07T14:00:00+09:00",
  "delay_minutes": 35,
  "last_checkpoint_type": null,
  "last_checkpoint_at": null,
  "latitude": null,
  "longitude": null
}
```

예상 결과:
- `delay_minutes >= 30` -> `reematch_candidate`
- `delay_minutes >= 60` -> `chain_break_candidate`

### `pawrelay:backup_exhausted`

```json
{
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": null,
  "activity_regions": ["충청남도", "대전광역시"]
}
```

예상 결과:
- `decision = shelter_recommend` 또는 `admin_alert`

### `pawrelay:ping_no_response`

```json
{
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "volunteer_name": "홍길동",
  "scheduled_time": "2026-05-07T14:00:00+09:00",
  "ping_sent_at": "2026-05-07T12:00:00+09:00",
  "ping_deadline_at": "2026-05-07T12:30:00+09:00",
  "activity_regions": ["충남"]
}
```

예상 결과:
- `decision = admin_alert`

### `pawrelay:pre_departure_no_show`

```json
{
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "volunteer_name": "홍길동",
  "scheduled_time": "2026-05-07T14:00:00+09:00",
  "ping_sent_at": "2026-05-07T12:00:00+09:00",
  "ping_responded_at": null,
  "activity_regions": ["Chungcheongnam-do"]
}
```

예상 결과:
- `decision = penalty_candidate`
- `requires_chain_break = true`
- `penalty_days = 30`

## 출력 Payload 예시

```json
{
  "event_type": "pre_departure_no_show",
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "decision": "penalty_candidate",
  "reason": "출발 전 노쇼가 감지되어 체인 해제와 30일 정지 후보로 분류했습니다.",
  "recommended_shelters": [],
  "requires_chain_break": true,
  "penalty_days": 30,
  "detected_at": "2026-05-07T14:35:00+09:00",
  "version": 1
}
```

## Decision Enum

- `shelter_recommend`
- `admin_alert`
- `no_show_candidate`
- `chain_break_candidate`
- `reematch_candidate`
- `penalty_candidate`

## 기준값

- `RE_MATCH_DELAY_MINUTES = 30`
- `CHAIN_BREAK_DELAY_MINUTES = 60`
- `NO_SHOW_PENALTY_DAYS = 30`
- `NEEDS_VERIFY_GRACE_MINUTES = 30`

## 참고

- 보호소 추천은 `data/shelter.json`을 기준으로 한다.
- AI는 판정만 수행하고, 실제 실행은 BE가 담당한다.
