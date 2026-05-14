# Week 6 Local Test Setup

## Goal

- Week 6 실시간 검증 전에 필요한 테스트 계정과 브라우저 구성을 빠르게 맞춘다.
- 봉사자, 보호소, 입양자 공개 조회를 서로 다른 세션으로 분리해서 동시에 확인한다.
- 현재 프론트/백엔드 기준으로 바로 확인 가능한 범위와 아직 막히는 범위를 구분한다.

## Recommended Browser Layout

### Window A - Volunteer

- 브라우저: 일반 Chrome 또는 Edge 프로필 1개
- 이유: Web Push, service worker, 알림 권한 확인이 필요하다.
- 로그인 계정: `vol1@test.com / Vol0111!`
- 기본 진입 경로: `/volunteer/posts`
- 실제 확인 경로:
  - `/volunteer/matching/{segment_id}`
  - 필요 시 `/volunteer/chat`

### Window B - Shelter Dashboard

- 브라우저: 시크릿 창 또는 다른 프로필
- 이유: 봉사자 세션과 쿠키가 섞이지 않도록 분리한다.
- 로그인 계정: `shelter1@test.com / Shelter1!`
- 기본 진입 경로: `/dashboard`
- 실제 확인 경로:
  - 보호소 대시보드 카드
  - 게시글 상세
  - `ping.confirmed`, `handover.no_response`, `departure.no_response` 상태 반영

### Window C - Adopter Public Tracking

- 브라우저: 별도 탭 또는 모바일 브라우저
- 인증: 불필요
- 진입 경로: `/track/{share_token}`
- `share_token` 확보 방법:
  - 보호소 대시보드 카드의 `입양자 현황 보기` 링크 클릭
  - 또는 `/posts/public/{share_token}` API 기준으로 동일 토큰 사용

## Seed Accounts

### Admin

- `admin@pawrelay.com / Admin1234!`

### Shelters

- `shelter1@test.com / Shelter1!`
- `shelter2@test.com / Shelter2!`
- `shelter3@test.com / Shelter3!`
- `shelter4@test.com / Shelter4!`

### Volunteers

- 기본 패턴: `vol{n}@test.com / Vol{NN}11!`
- 예:
  - `vol1@test.com / Vol0111!`
  - `vol2@test.com / Vol0211!`
  - `vol3@test.com / Vol0311!`

## Environment Checklist

### Required Services

- Docker Desktop 실행
- Postgres 실행
- Redis 실행
- 백엔드 실행
- 프론트 실행

### Quick Checks

- 프론트 확인: `http://127.0.0.1:3000`
- 백엔드 health 확인: `http://127.0.0.1:8000/health`
- 보호소 로그인 가능 여부 확인
- 봉사자 로그인 가능 여부 확인

## Browser Preparation

### Volunteer Window

- 알림 권한을 `허용`으로 설정한다.
- PWA install prompt가 뜨면 dismiss 여부를 기록한다.
- `Application > Service Workers`에서 worker 등록 여부를 확인한다.
- `Application > Push Messaging` 또는 알림 권한 상태를 확인한다.

### Shelter Window

- 로그인 직후 `/dashboard` 접근이 되는지 확인한다.
- 대시보드 카드에서 share link 버튼이 보이는지 확인한다.
- WebSocket 연결 실패 토스트나 콘솔 에러가 없는지 본다.

### Adopter Window

- `/track/{share_token}`로 진입한다.
- 현재 프론트는 public post API와 `checkpoint.updated` WebSocket을 연결한 상태다.
- 백엔드와 WebSocket이 정상 실행 중이면 체크포인트 갱신을 화면에서 바로 확인할 수 있다.

## Suggested Test Order

1. Window A에서 봉사자 로그인
2. Window B에서 보호소 로그인
3. Window C에서 share_token 링크 열기
4. Window A에서 알림 권한 허용
5. `/notifications/push/vapid-key` 응답 확인
6. `/notifications/push/subscribe` 성공 여부 확인
7. `ping_check` push 수신 확인
8. `ping.confirmed` 보호소 초록 상태 확인
9. `departure.no_response` 또는 `handover.no_response` 보호소 경고 상태 확인
10. `checkpoint.updated` 입양자 조회 반영 여부 확인

## Current Known Gaps

- Week 6의 `departure.no_response`는 `handover.no_response`와 다른 신규 이벤트로 분리하는 전제를 사용한다.
- `departure.no_response` 트리거가 아직 없으면 보호소 주황 경고 시나리오는 끝까지 확인하기 어렵다.
- 로컬에서 push/WebSocket을 보려면 프론트와 백엔드가 모두 정상 실행 중이어야 한다.

## Ready State Definition

- 봉사자 세션, 보호소 세션, 입양자 공개 조회 세션이 동시에 열려 있다.
- 봉사자 브라우저에서 알림 권한이 허용되어 있다.
- `share_token`이 확보되어 있다.
- 프론트와 백엔드 health가 모두 확인된다.
- 그 다음부터는 Week 6 e2e 체크리스트 순서대로 바로 검증할 수 있다.
