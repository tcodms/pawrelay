# Week5 Anomaly Detector Interface

## Overview

- 역할 분리: `BE 감지 -> AI 판정 -> BE 실행`
- AI는 DB 저장이나 REST 실행 없이 decision payload만 반환한다.

## Input Channels

- `pawrelay:sos`
- `pawrelay:needs_verify`
- `pawrelay:checkpoint_delay`

## Output Channel

- `pawrelay:ai:decision`

## Input Payloads

### `pawrelay:sos`

```json
{
  "segment_id": 1,
  "volunteer_id": 42,
  "latitude": 36.35,
  "longitude": 127.38,
  "activity_region": "충청남도"
}
```

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

## Output Payload

```json
{
  "event_type": "checkpoint_delay",
  "segment_id": 42,
  "chain_id": 7,
  "volunteer_id": 101,
  "decision": "chain_break_candidate",
  "reason": "scheduled_time 기준 35분 경과했고 checkpoint 기록이 없습니다.",
  "recommended_shelters": [],
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

## Config Assumptions

- `CHECKPOINT_DELAY_MINUTES=30`
- `NEEDS_VERIFY_GRACE_MINUTES=30`

## Notes

- `activity_regions`는 시/도 공식 명칭 배열을 사용한다.
- AI는 판정만 수행하고 후속 실행은 BE가 담당한다.
