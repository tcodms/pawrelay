# Week 6 Notification Templates

## Purpose

- Week 6 MVP 기준 역할별 알림 문구를 고정한다.
- Web Push, in-app notification, WebSocket UI 문구를 같은 톤으로 맞춘다.
- 실제 발송 로직은 BE가 담당하고, 이 문서는 문구 기준과 연결 대상을 정리한다.
- 현재 백엔드 구현에서 쓰는 `type`, `title`, `message`, `payload` 구조를 기준으로 작성한다.

## Template Field Rules

- `type`: 백엔드와 프론트가 공통으로 사용하는 이벤트/알림 키
- `title`: 짧은 제목. 알림 카드나 브라우저 푸시 제목으로 사용
- `message`: 사용자에게 바로 보이는 핵심 문구
- `url`: 푸시 클릭 시 이동할 경로. WebSocket 전용 이벤트는 생략 가능
- `payload`: 화면 분기나 상세 이동에 필요한 최소 필드만 포함

## Current Alignment Notes

- `ping_check`는 현재 백엔드에서 실제 push 알림으로 사용 중이다.
- `ping.confirmed`는 현재 `approve_handover()` 흐름에서 WebSocket 이벤트로 발행된다.
- `handover.no_response`는 현재 `handover_timeout` 기반 WebSocket/in-app 알림으로 본다.
- `departure.no_response`는 Week 6의 출발 전 미응답 경고용 신규 이벤트로 분리하는 것을 전제로 한다.
- `checkpoint.updated`는 현재 입양자 조회용 WebSocket 이벤트로 발행된다.
- 따라서 아래 템플릿은 Week 6 목표와 현재 구현 상태를 함께 맞추는 기준 문구로 본다.

## Volunteer

### `matching_proposed`

- type: `matching_proposed`
- title: `새 릴레이 제안이 도착했어요`
- message: `{animal_name} 이동 릴레이 제안이 도착했어요. 참여 가능 여부를 확인해주세요.`
- url: `/volunteer/matching/{segment_id}`
- payload: `{ segment_id, url }`
- notes: 매칭 제안 알림. 참여 수락/거절 화면으로 이동한다.

### `matching_confirmed`

- type: `matching_confirmed`
- title: `릴레이가 확정되었어요`
- message: `{origin} → {destination} 구간 릴레이가 확정되었어요. 인계 장소와 일정을 확인해주세요.`
- url: `/volunteer/matching/{segment_id}`
- payload: `{ segment_id, url }`
- notes: 확정 알림. 상세 구간, 인계 장소, 채팅 진입 링크를 안내한다.

### `ping_check`

- type: `ping_check`
- title: `곧 출발 시간이에요`
- message: `출발 2시간 전입니다. 운행 가능 여부를 확인해주세요.`
- url: `/volunteer/matching/{segment_id}`
- payload: `{ segment_id, scheduled_time, url }`
- notes: Week 6 핵심 Web Push. 봉사자 응답 유도용이다.

### `handover_waiting_confirm`

- type: `handover_waiting_confirm`
- title: `인계 확인이 필요해요`
- message: `상대 봉사자가 인계 코드를 입력했어요. 내 인계 확인을 진행해주세요.`
- url: `/volunteer/matching/{segment_id}`
- payload: `{ segment_id, url }`
- notes: handover verify 대기 상태 알림이다.

### `handover_location_changed`

- type: `handover_location_changed`
- title: `인계 장소가 변경되었어요`
- message: `인계 장소가 {waypoint_name}(으)로 변경되었어요. 이동 전에 다시 확인해주세요.`
- url: `/volunteer/matching/{segment_id}`
- payload: `{ segment_id, new_location, url }`
- notes: 변경된 waypoint 확인용 알림이다.

## Shelter

### `matching_failed`

- type: `matching_failed`
- title: `오늘 릴레이 매칭이 성사되지 않았어요`
- message: `현재 조건으로는 릴레이 연결이 어려웠어요. 일정이나 경로 조정이 필요한지 확인해주세요.`
- channel: `in_app` or dashboard banner
- payload: `{ transport_post_id }`
- notes: 배치 실패 알림.

### `ping.confirmed`

- event: `ping.confirmed`
- title: `봉사자 출발 확인 완료`
- message: `{volunteer_name} 님이 출발 가능하다고 응답했어요.`
- channel: `WebSocket`
- payload: `{ segment_id, volunteer_name }`
- notes: 보호소 대시보드에서 초록 상태 전환에 사용한다.

### `handover.no_response`

- event: `handover.no_response`
- title: `인계 확인 응답이 지연되고 있어요`
- message: `{volunteer_name} 님이 인계 확인에 아직 응답하지 않았어요. 인계 진행 상황을 확인해주세요.`
- channel: `WebSocket`
- payload: `{ segment_id, volunteer_name, scheduled_time }`
- notes: 인계 코드 입력 이후 30분 이상 응답이 없는 상황용 경고 이벤트다.

### `departure.no_response`

- event: `departure.no_response`
- title: `출발 확인 응답이 지연되고 있어요`
- message: `{volunteer_name} 님이 출발 확인에 아직 응답하지 않았어요. 출발 가능 여부를 확인해주세요.`
- channel: `WebSocket`
- payload: `{ segment_id, volunteer_name, scheduled_time }`
- notes: 출발 2시간 전 ping_check 발송 후, 출발 1시간 전까지 응답이 없는 상황용 경고 이벤트다.

### `delay_reported`

- event: `delay.reported`
- title: `지연 신고가 접수되었어요`
- message: `{volunteer_name} 님이 구간 지연을 신고했어요. 후속 이동 일정 확인이 필요합니다.`
- channel: `WebSocket` or `in_app`
- payload: `{ segment_id, message }`
- notes: 다음 구간 영향도 확인용 알림이다.

### `sos_triggered`

- event: `sos.triggered`
- title: `긴급 대응이 필요해요`
- message: `{volunteer_name} 님이 SOS를 보냈어요. 현재 위치와 보호 연계 가능 여부를 확인해주세요.`
- channel: `WebSocket` or `in_app`
- payload: `{ segment_id, latitude, longitude }`
- notes: 지도 연동 가능한 경우 위치 강조 표시와 함께 사용한다.

## Adopter

### `checkpoint.updated`

- event: `checkpoint.updated`
- title: `아이 이동 현황이 업데이트되었어요`
- message: `{checkpoint_label}이 기록되었어요. 현재 위치를 확인해주세요.`
- channel: `WebSocket UI`
- payload: `{ transport_post_id, segment_order, latitude, longitude, recorded_at }`
- notes: `checkpoint_label` 예시: `출발`, `중간 인계`, `최종 도착`

### `arrival_started`

- type: `arrival_started`
- title: `이동이 시작되었어요`
- message: `보호 동물의 이동이 시작되었어요. 실시간 위치를 확인할 수 있어요.`
- channel: `timeline UI`
- payload: `{ transport_post_id }`
- notes: 첫 departure 체크포인트 이후 표시할 수 있다.

### `arrival_completed`

- type: `arrival_completed`
- title: `이동이 완료되었어요`
- message: `보호 동물이 최종 목적지에 안전하게 도착했어요.`
- channel: `timeline UI`
- payload: `{ transport_post_id }`
- notes: 최종 arrival 완료 시 표시한다.

## Tone Rules

- 봉사자 문구는 행동 요청이 분명해야 한다.
- 보호소 문구는 현재 상황과 필요한 확인 포인트를 함께 전달한다.
- 입양자 문구는 불안감을 줄이고 진행 상태를 간결하게 보여준다.
- 같은 이벤트라도 Push와 WebSocket에서 핵심 의미는 유지한다.

## Mapping Summary

| role | event/type | primary channel |
|------|------------|-----------------|
| volunteer | `matching_proposed` | push + in-app |
| volunteer | `matching_confirmed` | push + in-app |
| volunteer | `ping_check` | push |
| volunteer | `handover_waiting_confirm` | push + in-app |
| volunteer | `handover_location_changed` | push + in-app |
| shelter | `matching_failed` | in-app |
| shelter | `ping.confirmed` | websocket |
| shelter | `handover.no_response` | websocket |
| shelter | `departure.no_response` | websocket |
| shelter | `delay_reported` | websocket |
| shelter | `sos_triggered` | websocket |
| adopter | `checkpoint.updated` | websocket |
| adopter | `arrival_started` | UI |
| adopter | `arrival_completed` | UI |

## Suggested Review Order

1. volunteer push 문구부터 확정
2. shelter dashboard websocket 문구 확정
3. adopter realtime 안내 문구 확정
4. 마지막으로 payload 필드와 url 경로를 프론트/백엔드와 교차 확인
