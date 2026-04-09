# ERD — PawRelay (12개 테이블)

---

## 테이블 관계

```
users ──────────────────────────────────────────────────────────
  │ 1:1  shelter_profiles
  │ 1:1  volunteer_profiles
  │ 1:N  transport_posts          (shelter_id)
  │ 1:N  volunteer_schedules      (volunteer_id)
  │ 1:N  relay_segments           (volunteer_id)
  │ 1:N  notifications            (user_id)
  │ 1:N  volunteer_history        (volunteer_id)
  └ 1:N  push_subscriptions       (user_id)

transport_posts ────────────────────────────────────────────────
  │ 1:N  volunteer_schedules      (post_id, nullable)
  │ 1:N  relay_chains             (transport_post_id)
  └ 1:N  notifications            (transport_post_id, nullable)

relay_chains ───────────────────────────────────────────────────
  └ 1:N  relay_segments           (chain_id)
         ※ 공고 1개에 active 상태 chain은 1개만 존재해야 함
            DB 제약 불가 → matching_service.py에서 체인 생성 전 확인

relay_segments ─────────────────────────────────────────────────
  │ 1:N  checkpoints              (segment_id)
  └ 1:1  volunteer_history        (segment_id)
```

---

## users

```
users
├── id                    BIGINT          PK, AUTO INCREMENT
├── email                 VARCHAR(255)    UNIQUE NOT NULL
├── password_hash         VARCHAR(255)    NOT NULL                  -- bcrypt 해시
├── name                  VARCHAR(100)    NOT NULL
├── role                  ENUM            NOT NULL                  -- shelter | volunteer | admin
├── email_verified_at     TIMESTAMPTZ     NULL                      -- 이메일 인증 완료 시각
├── account_status        ENUM            NOT NULL DEFAULT 'active' -- active | suspended | banned
├── created_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()
└── updated_at            TIMESTAMPTZ     NOT NULL DEFAULT NOW()    -- 계정 정지/해제 추적
```

---

## shelter_profiles

```
shelter_profiles
├── id                            BIGINT        PK, AUTO INCREMENT
├── user_id                       BIGINT        FK → users.id, UNIQUE NOT NULL
├── name                          VARCHAR(100)  NOT NULL              -- 보호소명
├── phone                         VARCHAR(20)   NOT NULL
├── email                         VARCHAR(255)  NOT NULL              -- 공고 알림 수신용 (users.email은 로그인용)
├── address                       VARCHAR(255)  NOT NULL
├── shelter_registration_doc_url  VARCHAR(500)  NULL                  -- 서류 S3 URL (위탁계약서, 보호소 등록증 등)
├── verification_notes            TEXT          NULL                  -- 관리자 검토 메모 (승인/거절 사유)
├── operating_hours               VARCHAR(100)  NULL                  -- ex) 09:00~18:00
└── verified_at                   TIMESTAMPTZ   NULL                  -- NULL이면 승인 대기 중
```

---

## volunteer_profiles

```
volunteer_profiles
├── id                  BIGINT          PK, AUTO INCREMENT
├── user_id             BIGINT          FK → users.id, UNIQUE NOT NULL
├── vehicle_available   BOOLEAN         NOT NULL DEFAULT false
├── max_animal_size     ENUM            NOT NULL                  -- small | medium | large
└── activity_regions    VARCHAR(50)[]   NOT NULL                  -- ex) {서울특별시, 경기도}
```

---

## transport_posts

```
transport_posts
├── id                BIGINT        PK, AUTO INCREMENT
├── shelter_id        BIGINT        FK → users.id, NOT NULL
├── status            ENUM          NOT NULL DEFAULT 'recruiting' -- recruiting | in_transit | completed | cancelled
├── animal_name       VARCHAR(50)   NOT NULL
├── animal_size       ENUM          NOT NULL                      -- small | medium | large
├── animal_photo_url  VARCHAR(500)  NULL                          -- S3 URL
├── animal_notes      TEXT          NULL                          -- 특이사항
├── origin            VARCHAR(255)  NOT NULL                      -- 출발지 텍스트
├── destination       VARCHAR(255)  NOT NULL                      -- 목적지 텍스트
├── scheduled_date    DATE          NOT NULL
├── share_token       UUID          UNIQUE NOT NULL DEFAULT gen_random_uuid()  -- 입양자 공개 조회용
├── created_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
└── updated_at        TIMESTAMPTZ   NOT NULL DEFAULT NOW()
```

---

## volunteer_schedules

```
volunteer_schedules
├── id                  BIGINT                    PK, AUTO INCREMENT
├── volunteer_id        BIGINT                    FK → users.id, NOT NULL
├── post_id             BIGINT                    FK → transport_posts.id, NULL  -- 게시판 진입 시 세팅
├── route_description   TEXT                      NOT NULL  -- ex) 광주 → 천안 (화면 표시용)
├── route               GEOMETRY(LineString,4326) NOT NULL  -- PostGIS 거리 계산용
├── available_date      DATE                      NOT NULL
├── origin_area         VARCHAR(100)              NOT NULL  -- ex) 광주광역시
├── destination_area    VARCHAR(100)              NOT NULL  -- ex) 충남 천안시
├── vehicle_available   BOOLEAN                   NOT NULL  -- 챗봇 입력 시점 스냅샷 (volunteer_profiles와 별개)
├── max_animal_size     ENUM                      NOT NULL  -- small | medium | large
├── status              ENUM                      NOT NULL DEFAULT 'available'  -- available | matched | expired
├── created_at          TIMESTAMPTZ               NOT NULL DEFAULT NOW()
└── updated_at          TIMESTAMPTZ               NOT NULL DEFAULT NOW()  -- status 변경 추적
```

---

## relay_chains

```
relay_chains
├── id                  BIGINT      PK, AUTO INCREMENT
├── transport_post_id   BIGINT      FK → transport_posts.id, NOT NULL
├── backup_candidates   JSONB       NULL  -- {"1": [vol_id, ...], "2": [...]}
├── matching_reason     TEXT        NULL  -- LLM 생성 매칭 사유
├── status              ENUM        NOT NULL DEFAULT 'proposed'  -- proposed | active | completed | broken
├── created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

---

## relay_segments

```
relay_segments
├── id                          BIGINT       PK, AUTO INCREMENT
├── chain_id                    BIGINT       FK → relay_chains.id, NOT NULL
├── volunteer_id                BIGINT       FK → users.id, NOT NULL
├── segment_order               SMALLINT     NOT NULL               -- 구간 순서 (1, 2, 3...)
├── pickup_location             VARCHAR(255) NOT NULL               -- 인수 장소
├── dropoff_location            VARCHAR(255) NOT NULL               -- 인계 장소 (waypoints 1순위 기본값)
├── scheduled_time              TIMESTAMPTZ  NOT NULL               -- 예정 출발 시각
├── estimated_arrival           TIMESTAMPTZ  NULL                   -- 예상 도착 시각 (체인 연결 검증용)
│                                                                   -- prev.estimated_arrival + 30분 <= next.scheduled_time
├── handover_code               CHAR(6)      NULL                   -- 6자리 인계 코드 (당일 00:00 노출)
├── handover_code_given_at      TIMESTAMPTZ  NULL                   -- 앞 구간 봉사자 코드 입력 시각
├── handover_code_received_at   TIMESTAMPTZ  NULL                   -- 뒷 구간 봉사자 코드 입력 시각
├── handover_method             ENUM         NULL                   -- code | manual_approval
├── ping_sent_at                TIMESTAMPTZ  NULL                   -- 출발 2시간 전 핑 발송 시각
├── ping_responded_at           TIMESTAMPTZ  NULL                   -- 봉사자 핑 응답 시각 (NULL이면 미응답)
├── status                      ENUM         NOT NULL DEFAULT 'pending'
│                                                                   -- pending | accepted | in_progress
│                                                                   -- completed | needs_verification | no_show
├── accepted_at                 TIMESTAMPTZ  NULL
├── declined_at                 TIMESTAMPTZ  NULL
├── decline_reason              TEXT         NULL                   -- 거절 사유
└── updated_at                  TIMESTAMPTZ  NOT NULL DEFAULT NOW() -- status 전환 시각 추적
```

---

## checkpoints

```
checkpoints
├── id           BIGINT        PK, AUTO INCREMENT
├── segment_id   BIGINT        FK → relay_segments.id, NOT NULL
├── type         ENUM          NOT NULL  -- departure | waypoint | arrival
├── latitude     DECIMAL(9,6)  NULL      -- GPS 거부 시 null 허용
├── longitude    DECIMAL(9,6)  NULL      -- GPS 거부 시 null 허용
└── recorded_at  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
```

---

## volunteer_history

```
volunteer_history
├── id            BIGINT        PK, AUTO INCREMENT
├── volunteer_id  BIGINT        FK → users.id, NOT NULL
├── segment_id    BIGINT        FK → relay_segments.id, UNIQUE NOT NULL
├── distance_km   DECIMAL(6,2)  NOT NULL
└── completed_at  TIMESTAMPTZ   NOT NULL
```

---

## waypoints

```
waypoints
├── id       BIGINT                  PK, AUTO INCREMENT
├── name     VARCHAR(100)            NOT NULL  -- ex) 천안휴게소
├── type     ENUM                    NOT NULL  -- rest_area | train | bus | shelter
├── address  VARCHAR(255)            NOT NULL
├── phone    VARCHAR(20)             NULL      -- shelter 타입만 해당
├── geom     GEOMETRY(Point, 4326)   NOT NULL  -- PostGIS
└── source   VARCHAR(50)             NOT NULL  -- 공공데이터포털 출처
```

---

## notifications

```
notifications
├── id                  BIGINT      PK, AUTO INCREMENT
├── user_id             BIGINT      FK → users.id, NOT NULL
├── transport_post_id   BIGINT      FK → transport_posts.id, NULL
├── type                VARCHAR(50) NOT NULL
│                                   -- matching_proposed | matching_confirmed | ping_check
│                                   -- ping_no_response | delay_reported | sos_triggered
│                                   -- handover_waiting_confirm | handover_location_changed | matching_failed
├── channel             ENUM        NOT NULL   -- in_app | email | push
├── payload             JSONB       NOT NULL   -- 알림 본문 데이터
├── status              ENUM        NOT NULL DEFAULT 'pending'  -- pending | sent | failed
├── retry_count         SMALLINT    NOT NULL DEFAULT 0
├── sent_at             TIMESTAMPTZ NULL
├── read_at             TIMESTAMPTZ NULL
└── created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW()
```

---

## push_subscriptions

```
push_subscriptions
├── id          BIGINT      PK, AUTO INCREMENT
├── user_id     BIGINT      FK → users.id, NOT NULL
├── endpoint    TEXT        NOT NULL  -- Web Push 엔드포인트 URL
├── p256dh      TEXT        NOT NULL  -- 암호화 키
├── auth        TEXT        NOT NULL  -- 인증 시크릿
├── created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
└── UNIQUE(user_id, endpoint)         -- 동일 기기 중복 구독 방지
```

---

## 인덱스

| 테이블 | 컬럼 | 종류 | 이유 |
|--------|------|------|------|
| users | email | UNIQUE | 로그인 조회 |
| transport_posts | share_token | UNIQUE | 입양자 조회 |
| transport_posts | status, scheduled_date | 복합 | 공고 목록 필터 |
| volunteer_schedules | volunteer_id | 단일 | 봉사 이력 조회 (GET /volunteers/history) |
| volunteer_schedules | route | GiST | PostGIS 근접 필터 (배치 매칭 1단계) |
| volunteer_schedules | available_date, status | 복합 | 배치 매칭 대상 조회 |
| relay_chains | transport_post_id | 단일 | 공고별 체인 조회 |
| relay_segments | chain_id | 단일 | 체인별 구간 조회 |
| relay_segments | volunteer_id, status | 복합 | 봉사자 구간 조회 |
| checkpoints | segment_id | 단일 | 구간별 체크포인트 조회 |
| waypoints | geom | GiST | 인근 waypoint 조회 |
| notifications | user_id, read_at | 복합 | 읽지 않은 알림 조회 |
| push_subscriptions | user_id, endpoint | UNIQUE | 중복 구독 방지 |
