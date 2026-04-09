# PawRelay 프론트엔드 (Frontend) AI 코딩 가이드라인

본 문서는 PawRelay 프로젝트의 프론트엔드 개발을 위한 절대적인 규칙입니다. **모든 코드는 `docs/api-spec.md`와 `docs/design.md`를 최우선으로 준수하여 작성해야 합니다.**

## 🚫 1. 절대 금지 사항 (충돌 방지)
- `backend/` 및 `ai/` 디렉토리는 절대 생성, 수정, 삭제하지 마세요. (API가 필요하면 백엔드 담당자에게 요청)
- 임의로 API 엔드포인트 경로를 지어내거나 변경하지 마세요.
- 노쇼 처리 UI 개발 시 '자동 페널티 부여' 버튼을 만들지 마세요. (서버 자동화 또는 관리자 수동 처리 영역임)

## 🛠 2. 기술 스택 및 환경
- **Framework**: Next.js 14 (App Router 필수)
- **Language**: TypeScript (모든 응답/요청 인터페이스 정의 필수)
- **Styling**: Tailwind CSS
- **PWA**: `@ducanh2912/next-pwa` 사용 (구버전 `next-pwa` 절대 사용 금지)
- **지도 API**: 카카오맵 API (`NEXT_PUBLIC_KAKAO_MAP_API_KEY`) - 렌더링 전용
- **위치 API**: Web Geolocation API (`navigator.geolocation`) - 별도 패키지 설치 금지

## 🔐 3. 인증 및 API 통신 규칙 (가장 중요)
- **토큰 처리**: Access Token과 Refresh Token은 모두 백엔드에서 **`httpOnly` 쿠키**로 구워줍니다.
- **헤더 금지**: Axios나 Fetch 요청 시 `Authorization: Bearer ...` 헤더를 **절대 수동으로 넣지 마세요.** (브라우저가 쿠키를 자동 전송함)
- **에러 응답 포맷**: 백엔드 에러는 항상 `{ "error": "ERROR_CODE" }` 형태입니다. (`error.detail`이나 `error.message` 사용 금지)
- **토큰 갱신 (인터셉터)**: API 호출 시 `401 Unauthorized` 에러가 발생하면, body 없이 `POST /auth/refresh`를 호출하여 쿠키를 갱신하고 원래 요청을 재시도하세요. (갱신 실패 시 로그인 페이지로 리다이렉트)

## 📡 4. 실시간 통신 (WebSocket)
- **연결 주소 (2가지 분기)**:
  - 로그인 유저 (보호소 대시보드): `ws://api/ws` (쿠키로 자동 인증)
  - 입양자 조회 (비로그인): `ws://api/ws?share_token={token}`
- **이벤트 처리**: `ping.confirmed`, `ping.no_response`, `checkpoint.updated` 등의 이벤트를 수신하여 전역 상태를 업데이트하세요.
- **재연결 폴백**: 소켓 재연결 시 반드시 `GET /notifications/unread`를 호출하여 밀린 알림을 동기화하세요.

## 📱 5. 디렉토리 및 주요 화면 라우팅
- `/dashboard/*`: 보호소 웹 대시보드 (데스크탑 최적화)
- `/volunteer/*`: 봉사자 PWA (모바일 최적화)
- `/track/[token]`: 입양자 실시간 이송 현황 (로그인 불필요, 미들웨어 보호 해제 필수)

## 🤖 6. 핵심 비즈니스 로직 UI 규칙
- **봉사자 챗봇 (`/volunteer/chat`)**: 
  - LLM이 아닌 상태 머신입니다. `POST /chatbot/message` 응답의 `input_type` (`address_search`, `date_picker`, `buttons`)에 따라 UI 모달/위젯을 렌더링하세요. 직접 텍스트를 입력하는 채팅창은 기본적으로 숨깁니다.
  - `session_id`는 `sessionStorage`에 관리하세요.
- **인계 확인 화면 (`/volunteer/handover`)**: 
  - 메인 플로우: **6자리 인계 코드 수동 입력**
  - 폴백 플로우: [인계 완료 요청] 버튼 (상대방에게 승인 푸시 알림 전송)
- **지도 및 Geocoding**: 
  - 프론트는 카카오맵 SDK 렌더링만 담당합니다. 주소를 좌표로 변환(Geocoding)하여 DB에 저장하는 로직은 백엔드 API가 수행합니다.
- **체크포인트 위치 수집**: 
  - `navigator.geolocation` 사용 중 사용자가 위치 권한을 거부하면 에러를 띄우지 말고, `latitude`, `longitude`를 `null`로 세팅하여 전송하세요. 단, 화면에 "위치 정보 없이 기록됩니다"라고 안내하세요.

## 🍏 7. PWA 및 iOS 제약 사항
- iOS 16.4 이상은 '홈 화면에 추가'를 완료해야만 Push 알림 권한 획득이 가능합니다.
- 봉사자 온보딩 화면에서 OS를 감지하여 iOS일 경우 '홈 화면 추가 방법'을 시각적으로 안내하는 UI를 반드시 구현하세요.