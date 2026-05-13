# Week 6 Realtime E2E Checklist

## Scope

- 출발 2시간 전 `ping_check` Web Push 발송 확인
- 봉사자 응답 후 `ping.confirmed` 반영 확인
- 미응답 경고 시 `handover.no_response`, `departure.no_response` 반영 확인
- `checkpoint.updated` 입양자 실시간 조회 반영 확인
- Anomaly Detector 이벤트 입력과 decision 연결 확인

## Preconditions

- volunteer 계정으로 브라우저 알림 권한 허용이 가능해야 한다.
- 보호소 계정과 입양자 `share_token` 테스트 데이터가 준비되어 있어야 한다.
- `notifications`, `push_subscriptions`, `relay_segments`, `relay_checkpoints`를 조회할 수 있어야 한다.
- Redis, scheduler, websocket subscriber, AI worker가 모두 실행 중이어야 한다.

## Current Behavior Notes

- `ping_check`는 `departure_ping` 스케줄러에서 push 발송된다.
- `ping.confirmed`는 현재 `approve_handover()` 이후 websocket 이벤트로 발행된다.
- `handover.no_response`는 현재 stale handover timeout 이후 websocket/in-app으로 발행된다.
- `departure.no_response`는 Week 6의 출발 전 미응답 경고용 신규 이벤트로 분리하는 것을 전제로 한다.
- 따라서 Week 6 검증 시 두 이벤트를 같은 것으로 보지 않고, 트리거 조건을 구분해서 확인해야 한다.

## Payload Contracts

### Web Push `ping_check`

```json
{
  "type": "ping_check",
  "message": "출발 2시간 전입니다. 운행 가능 여부를 확인해주세요.",
  "segment_id": 42,
  "url": "/volunteer/matching/42"
}
```

Expected fields:
- `type`
- `message`
- `segment_id`
- `url`

### WebSocket `ping.confirmed`

```json
{
  "event": "ping.confirmed",
  "payload": {
    "segment_id": 42,
    "volunteer_name": "홍길동"
  }
}
```

Expected fields:
- `event`
- `payload.segment_id`
- `payload.volunteer_name`

### WebSocket `handover.no_response`

```json
{
  "event": "handover.no_response",
  "payload": {
    "segment_id": 42,
    "volunteer_name": "홍길동",
    "scheduled_time": "2026-05-15T11:00:00+09:00"
  }
}
```

Expected fields:
- `event`
- `payload.segment_id`
- `payload.volunteer_name`
- `payload.scheduled_time`

### WebSocket `departure.no_response`

```json
{
  "event": "departure.no_response",
  "payload": {
    "segment_id": 42,
    "volunteer_name": "홍길동",
    "scheduled_time": "2026-05-15T11:00:00+09:00"
  }
}
```

Expected fields:
- `event`
- `payload.segment_id`
- `payload.volunteer_name`
- `payload.scheduled_time`

### WebSocket `checkpoint.updated`

```json
{
  "event": "checkpoint.updated",
  "payload": {
    "transport_post_id": 12,
    "segment_order": 2,
    "latitude": 36.35,
    "longitude": 127.38,
    "recorded_at": "2026-05-15T10:20:00+09:00"
  }
}
```

Expected fields:
- `event`
- `payload.transport_post_id`
- `payload.segment_order`
- `payload.latitude`
- `payload.longitude`
- `payload.recorded_at`

## AI Event Mapping

| source event | AI input channel | expected AI decision |
|--------------|------------------|----------------------|
| `departure.no_response` | `pawrelay:ping_no_response` | `admin_alert` or `penalty_candidate` |
| delayed checkpoint | `pawrelay:checkpoint_delay` | `reematch_candidate` or `chain_break_candidate` |
| SOS report | `pawrelay:sos` | `shelter_recommend` or `admin_alert` |
| stale handover | `pawrelay:needs_verify` | `no_show_candidate` |

## Manual E2E Scenarios

### 1. Web Push Subscription

- volunteer 브라우저에서 알림 권한을 허용한다.
- `GET /notifications/push/vapid-key` 응답을 먼저 확인한다.
- `POST /notifications/push/subscribe`가 성공하는지 확인한다.
- DB에 `push_subscriptions` row가 생기는지 확인한다.

Expected:
- 서버 응답 `200 { "ok": true }`
- 동일 브라우저 재구독 시 중복 저장이 발생하지 않는다.

### 2. Departure Ping Scheduler

- `relay_segments.status = accepted`
- `scheduled_time`을 현재 시각 기준 2시간 이내로 맞춘다.
- scheduler 실행 또는 대기 후 push 발송을 확인한다.
- 로그에서 `departure_ping` 관련 발송 기록을 확인한다.

Expected:
- volunteer 디바이스에 `ping_check` push 도착
- `ping_sent_at` 기록
- `notifications` row 저장

### 3. Ping Confirmed

- 봉사자 응답 흐름을 실행한다.
- `ping_responded_at`이 저장되는지 확인한다.
- 보호소 대시보드 WebSocket에서 `ping.confirmed` 이벤트를 받는지 확인한다.

Expected:
- shelter dashboard 상태가 초록으로 전환
- 동일 segment 재응답 시 중복 상태 반영이 발생하지 않는다.

### 4. Ping No Response

- `ping_sent_at`은 있으나 `ping_responded_at`은 없는 상태를 만든다.
- 미응답 기준 시간을 넘긴다.
- 보호소 대시보드 WebSocket 이벤트를 확인한다.
- `notifications` unread 목록에도 반영되는지 확인한다.

Expected:
- `departure.no_response` 또는 `handover.no_response` 이벤트 수신
- shelter dashboard 상태가 주황으로 전환
- 필요 시 in-app notification도 함께 생성

### 5. Checkpoint Updated

- relay checkpoint를 저장한다.
- 입양자 조회 화면을 `share_token`으로 열어둔다.
- websocket 연결 유지 상태에서 새 체크포인트를 기록한다.

Expected:
- `checkpoint.updated` 이벤트 수신
- 지도/타임라인이 새 좌표와 시각으로 갱신

### 6. AI Integration

- `departure.no_response`, `checkpoint_delay`, `needs_verify`, `sos`를 각각 발생시킨다.
- Redis publish 이후 AI worker와 `pawrelay:ai:decision` subscriber 로그를 확인한다.
- backend subscriber가 실제 후속 처리하는 decision과 deferred 처리하는 decision을 구분해서 본다.

Expected:
- 입력 이벤트별로 decision payload가 생성
- `no_show_candidate`, `chain_break_candidate`는 BE 후속 처리로 이어짐
- `shelter_recommend`, `admin_alert`, `rematch_candidate`는 현재 구현 범위에 맞는 후속 처리 여부를 확인

## Open Checks

- `ping.confirmed`가 handover approve 재사용인지, 출발 전 ping 응답 전용 흐름인지 최종 명시 필요
- `handover.no_response`와 `departure.no_response`의 프론트 처리 분기 방식 확정 필요
- AI decision subscriber에서 `shelter_recommend`, `admin_alert`, `rematch_candidate` 후속 처리 범위 확인 필요

## Quick Pass Criteria

- push 구독 성공
- `ping_check` 1회 이상 수신
- `ping.confirmed` 이벤트 수신
- `handover.no_response` 또는 `departure.no_response` 이벤트 수신
- `checkpoint.updated` 이벤트 수신
- AI decision 로그 1회 이상 확인

## Done Criteria

- 봉사자 디바이스에서 `ping_check` push 수신 확인
- 보호소 대시보드에서 초록/주황 상태 전환 확인
- 입양자 조회 화면에서 `checkpoint.updated` 실시간 반영 확인
- 최소 1개 이상 AI anomaly 입력 이벤트가 decision까지 연결되는 것 확인
