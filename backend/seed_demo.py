"""
데모용 목업 데이터 시드 스크립트

시나리오:
  - 보호소 4곳 (광주/부산/전주/대전), 공고 4개씩 = 총 16개
  - 봉사자 20명:
      5명 — 특정 공고 직접 지원 (post_id 연결)
      15명 — 독립 동선 등록 (post_id=NULL)
  - 기존 DB 데이터 전체 초기화 후 재생성
  - 동물 사진은 S3에 업로드 후 S3 URL 사용

실행:
  cd backend
  python seed_demo.py
"""

import asyncio
import io
import os
import sys
import urllib.request
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from datetime import date, datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.s3 import get_s3_client
from app.core.security import hash_password
from app.models.user import User, ShelterProfile, VolunteerProfile
from app.models.post import TransportPost

DEMO_DATE = date(2026, 5, 10)

engine = create_async_engine(settings.database_url, echo=False, connect_args={"ssl": "require"})
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

# ── 프론트 dummy-posts.ts 에서 가져온 Unsplash 사진 ────────────────────────────
UNSPLASH = {
    "choco":  "https://images.unsplash.com/photo-1552053831-71594a27632d?w=400",
    "bboppi": "https://images.unsplash.com/photo-1587300003388-59208cc962cb?w=400",
    "nabi":   "https://images.unsplash.com/photo-1543466835-00a7907e9de1?w=400",
    "mongyi": "https://images.unsplash.com/photo-1518717758536-85ae29035b6d?w=400",
    "kkami":  "https://images.unsplash.com/photo-1477884213360-7e9d7dcc1e48?w=400",
    "dog1":   "https://images.unsplash.com/photo-1561037404-61cd46aa615b?w=400",
    "dog2":   "https://images.unsplash.com/photo-1537151608828-ea2b11777ee8?w=400",
    "dog3":   "https://images.unsplash.com/photo-1529429617124-95b109e86bb8?w=400",
    "cat1":   "https://images.unsplash.com/photo-1533738363-b7f9aef128ce?w=400",
}


def upload_photo_to_s3(key: str, unsplash_url: str) -> str:
    """Unsplash 이미지를 다운로드해 S3에 업로드하고 S3 URL 반환."""
    print(f"  [upload] {key} ...", end=" ", flush=True)
    try:
        req = urllib.request.Request(
            unsplash_url,
            headers={"User-Agent": "Mozilla/5.0 PawRelaySeed/1.0"},
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()

        s3 = get_s3_client()
        s3_key = f"animals/seed_{key}_{uuid.uuid4().hex[:8]}.jpg"
        s3.put_object(
            Bucket=settings.aws_s3_bucket,
            Key=s3_key,
            Body=data,
            ContentType="image/jpeg",
        )
        url = f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{s3_key}"
        print("✓")
        return url
    except Exception as e:
        print(f"✗ ({e}) — Unsplash URL 사용")
        return unsplash_url


def upload_all_photos() -> dict[str, str]:
    print("── S3 사진 업로드 ────────────────────────────────────")
    return {key: upload_photo_to_s3(key, url) for key, url in UNSPLASH.items()}


async def wipe_all(db: AsyncSession) -> None:
    """기존 데모 관련 데이터 전체 초기화."""
    print("── 기존 데이터 초기화 ────────────────────────────────")
    demo_emails = (
        ["admin@pawrelay.com"]
        + [f"shelter{i}@test.com" for i in range(1, 5)]
        + [f"vol{i}@test.com" for i in range(1, 21)]
    )
    result = await db.execute(
        text("SELECT id FROM users WHERE email = ANY(:emails)"),
        {"emails": demo_emails},
    )
    ids = [row[0] for row in result.fetchall()]
    if ids:
        await db.execute(text("DELETE FROM relay_segments WHERE volunteer_id = ANY(:ids)"), {"ids": ids})
        await db.execute(text("""
            DELETE FROM relay_chains WHERE transport_post_id IN (
                SELECT id FROM transport_posts WHERE shelter_id = ANY(:ids)
            )
        """), {"ids": ids})
        await db.execute(text("DELETE FROM volunteer_schedules WHERE volunteer_id = ANY(:ids)"), {"ids": ids})
        await db.execute(text("DELETE FROM transport_posts WHERE shelter_id = ANY(:ids)"), {"ids": ids})
        await db.execute(text("DELETE FROM shelter_profiles WHERE user_id = ANY(:ids)"), {"ids": ids})
        await db.execute(text("DELETE FROM volunteer_profiles WHERE user_id = ANY(:ids)"), {"ids": ids})
        await db.execute(text("DELETE FROM users WHERE id = ANY(:ids)"), {"ids": ids})
    print("  기존 데이터 삭제 완료")


def make_user(email: str, password: str, name: str, role: str) -> User:
    return User(
        email=email,
        password_hash=hash_password(password),
        name=name,
        role=role,
        email_verified_at=datetime.now(tz=timezone.utc),
        account_status="active",
    )


VOL_NAMES = [
    "김봉사", "이릴레이", "박서울", "최자원", "정봉사",
    "홍길동", "황봉사", "윤릴레이", "신봉사", "오릴레이",
    "장도움", "임봉사", "한릴레이", "조서울", "송봉사",
    "권도움", "민릴레이", "유봉사", "나릴레이", "강서울",
]


async def seed():
    # 1. S3 사진 업로드 (동기)
    photo = upload_all_photos()

    async with AsyncSessionLocal() as db:
        # 2. 기존 데이터 초기화
        await wipe_all(db)

        print("── 유저 생성 ──────────────────────────────────────")

        # ── Admin ─────────────────────────────────────────────────────────────
        admin = make_user("admin@pawrelay.com", "Admin1234!", "관리자", "admin")
        db.add(admin)

        # ── 보호소 4곳 ──────────────────────────────────────────────────────────
        shelter_info = [
            ("shelter1@test.com", "Shelter1!", "행복동물보호소",   "광주광역시 북구 운암동",    "062-111-0001"),
            ("shelter2@test.com", "Shelter2!", "사랑동물보호소",   "부산광역시 해운대구 좌동",  "051-222-0002"),
            ("shelter3@test.com", "Shelter3!", "희망동물보호소",   "전라북도 전주시 완산구",    "063-333-0003"),
            ("shelter4@test.com", "Shelter4!", "따뜻한동물보호소", "대전광역시 유성구 지족동",  "042-444-0004"),
        ]
        shelter_users = []
        for email, pw, name, addr, phone in shelter_info:
            u = make_user(email, pw, name, "shelter")
            db.add(u)
            shelter_users.append((u, addr, phone))

        await db.flush()

        for u, addr, phone in shelter_users:
            db.add(ShelterProfile(
                user_id=u.id, name=u.name,
                phone=phone, email=u.email,
                address=addr,
                verified_at=datetime.now(tz=timezone.utc),
            ))

        # ── 봉사자 20명 ──────────────────────────────────────────────────────────
        vols = []
        for i, name in enumerate(VOL_NAMES, start=1):
            u = make_user(f"vol{i}@test.com", f"Vol{i:02d}11!", name, "volunteer")
            db.add(u)
            vols.append(u)

        await db.flush()

        vol_profiles = [
            (True,  "small",  ["광주광역시", "충청남도"]),       # 1 김봉사
            (True,  "small",  ["충청남도", "경기도"]),            # 2 이릴레이
            (True,  "medium", ["경기도", "서울특별시"]),          # 3 박서울
            (True,  "medium", ["부산광역시", "대구광역시"]),      # 4 최자원
            (True,  "small",  ["부산광역시", "충청북도"]),        # 5 정봉사
            (True,  "medium", ["충청북도", "서울특별시"]),        # 6 홍길동
            (True,  "medium", ["전라북도", "충청남도"]),          # 7 황봉사
            (True,  "small",  ["충청남도", "경기도"]),            # 8 윤릴레이
            (True,  "medium", ["경기도", "서울특별시"]),          # 9 신봉사
            (True,  "large",  ["대전광역시", "충청남도"]),        # 10 오릴레이
            (True,  "medium", ["충청남도", "서울특별시"]),        # 11 장도움
            (False, "small",  ["광주광역시", "전라북도"]),        # 12 임봉사
            (True,  "medium", ["전라북도", "충청남도"]),          # 13 한릴레이
            (True,  "small",  ["충청남도", "인천광역시"]),        # 14 조서울
            (True,  "small",  ["경기도", "인천광역시"]),          # 15 송봉사
            (True,  "medium", ["부산광역시", "경상남도"]),        # 16 권도움
            (True,  "medium", ["대구광역시", "충청북도"]),        # 17 민릴레이
            (True,  "medium", ["충청북도", "경기도"]),            # 18 유봉사
            (False, "small",  ["경기도", "서울특별시"]),          # 19 나릴레이
            (True,  "large",  ["대전광역시", "서울특별시"]),      # 20 강서울
        ]
        for vol, (vehicle, size, regions) in zip(vols, vol_profiles):
            db.add(VolunteerProfile(
                user_id=vol.id,
                vehicle_available=vehicle,
                max_animal_size=size,
                activity_regions=regions,
            ))

        # ── 공고 16개 ────────────────────────────────────────────────────────────
        s1, s2, s3, s4 = [u for u, *_ in shelter_users]

        posts_spec = [
            # (shelter_user, 동물명, 크기, 출발지, 목적지, photo_key)
            (s1, "초코",  "small",  "광주광역시 북구 운암동",         "서울특별시 강남구 역삼동",   "choco"),
            (s1, "달이",  "small",  "광주광역시 북구 용봉동",         "경기도 고양시 일산동구",     "nabi"),
            (s1, "보리",  "medium", "광주광역시 서구 화정동",         "인천광역시 남동구 구월동",   "dog1"),
            (s1, "하늘",  "small",  "광주광역시 동구 계림동",         "경기도 수원시 영통구",       "cat1"),

            (s2, "뽀삐",  "medium", "부산광역시 해운대구 좌동",       "대구광역시 수성구 범어동",   "bboppi"),
            (s2, "루나",  "small",  "부산광역시 남구 용호동",         "서울특별시 마포구 합정동",   "dog2"),
            (s2, "코코",  "small",  "부산광역시 동래구 온천동",       "경기도 성남시 분당구",       "nabi"),
            (s2, "마루",  "large",  "부산광역시 북구 덕천동",         "대전광역시 유성구 궁동",     "kkami"),

            (s3, "몽이",  "medium", "전라북도 전주시 완산구 효자동",  "경기도 고양시 덕양구",       "mongyi"),
            (s3, "봄이",  "small",  "전라북도 전주시 덕진구 금암동",  "서울특별시 송파구 잠실동",   "dog3"),
            (s3, "토리",  "small",  "전라북도 전주시 완산구 평화동",  "인천광역시 부평구 부평동",   "cat1"),
            (s3, "두부",  "medium", "전라북도 전주시 덕진구 우아동",  "경기도 수원시 팔달구",       "dog1"),

            (s4, "까미",  "large",  "대전광역시 유성구 지족동",       "서울특별시 송파구 문정동",   "kkami"),
            (s4, "솜이",  "small",  "대전광역시 서구 둔산동",         "인천광역시 남동구 만수동",   "nabi"),
            (s4, "쫑이",  "medium", "대전광역시 동구 용전동",         "경기도 고양시 일산서구",     "bboppi"),
            (s4, "별이",  "small",  "대전광역시 중구 은행동",         "경기도 수원시 장안구",       "dog2"),
        ]

        posts = []
        for shelter_user, name, size, origin, dest, photo_key in posts_spec:
            p = TransportPost(
                shelter_id=shelter_user.id,
                status="recruiting",
                animal_name=name,
                animal_size=size,
                animal_photo_url=photo[photo_key],
                animal_notes="순한 편, 이동장 이용 가능",
                origin=origin,
                destination=dest,
                scheduled_date=DEMO_DATE,
            )
            db.add(p)
            posts.append(p)

        await db.flush()

        # 직접 지원 5개 공고 (post_id 연결할 봉사자용)
        p_choco  = posts[0]   # 초코 광주→서울
        p_bboppi = posts[4]   # 뽀삐 부산→대구
        p_luna   = posts[5]   # 루나 부산→서울
        p_mongyi = posts[8]   # 몽이 전주→고양
        p_kkami  = posts[12]  # 까미 대전→서울

        # ── 봉사자 스케줄 20개 ───────────────────────────────────────────────────
        # 좌표 기준: (경도 위도)
        # 광주 126.85,35.16 / 충남(천안) 127.15,36.81 / 경기(수원) 127.01,37.26
        # 서울 127.02,37.54 / 고양 126.83,37.66       / 인천 126.70,37.45
        # 부산 129.07,35.18 / 대구 128.60,35.87       / 충북(청주) 127.49,36.64
        # 전북(전주) 127.15,35.82 / 대전 127.39,36.35

        await db.execute(text("""
            INSERT INTO volunteer_schedules
              (volunteer_id, post_id, route_description,
               origin_area, destination_area,
               available_date, available_time, estimated_arrival_time,
               vehicle_available, max_animal_size, status, route)
            VALUES
              -- ① 김봉사: 광주→충남 [직접지원: 초코]
              (:v1, :p_choco, '광주에서 천안까지 차량',
               '광주광역시', '충청남도', :dt, '08:00', '12:00', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(126.85 35.16, 127.15 36.81)', 4326)),

              -- ② 이릴레이: 충남→경기 [독립]
              (:v2, NULL, '천안에서 수원까지 차량',
               '충청남도', '경기도', :dt, '13:00', '16:00', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.15 36.81, 127.01 37.26)', 4326)),

              -- ③ 박서울: 경기→서울 [독립]
              (:v3, NULL, '수원에서 서울까지 차량',
               '경기도', '서울특별시', :dt, '17:00', '19:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.01 37.26, 127.02 37.54)', 4326)),

              -- ④ 최자원: 부산→대구 [직접지원: 뽀삐]
              (:v4, :p_bboppi, '부산에서 대구까지 차량',
               '부산광역시', '대구광역시', :dt, '09:00', '11:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(129.07 35.18, 128.60 35.87)', 4326)),

              -- ⑤ 정봉사: 부산→충북 [직접지원: 루나]
              (:v5, :p_luna, '부산에서 청주까지 차량',
               '부산광역시', '충청북도', :dt, '07:00', '12:00', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(129.07 35.18, 127.49 36.64)', 4326)),

              -- ⑥ 홍길동: 충북→서울 [독립]
              (:v6, NULL, '청주에서 서울까지 차량',
               '충청북도', '서울특별시', :dt, '13:00', '17:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.49 36.64, 127.02 37.54)', 4326)),

              -- ⑦ 황봉사: 전북→충남 [직접지원: 몽이]
              (:v7, :p_mongyi, '전주에서 천안까지 차량',
               '전라북도', '충청남도', :dt, '08:00', '11:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.15 35.82, 127.15 36.81)', 4326)),

              -- ⑧ 윤릴레이: 충남→경기 [독립]
              (:v8, NULL, '천안에서 고양까지 차량',
               '충청남도', '경기도', :dt, '12:00', '15:30', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.15 36.81, 126.83 37.66)', 4326)),

              -- ⑨ 신봉사: 경기→서울 [독립]
              (:v9, NULL, '수원에서 서울까지 차량',
               '경기도', '서울특별시', :dt, '17:00', '19:30', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.01 37.26, 127.02 37.54)', 4326)),

              -- ⑩ 오릴레이: 대전→충남 [직접지원: 까미]
              (:v10, :p_kkami, '대전에서 천안까지 차량',
               '대전광역시', '충청남도', :dt, '09:00', '11:00', true, 'large', 'available',
               ST_GeomFromText('LINESTRING(127.39 36.35, 127.15 36.81)', 4326)),

              -- ⑪ 장도움: 충남→서울 [독립]
              (:v11, NULL, '천안에서 서울까지 차량',
               '충청남도', '서울특별시', :dt, '12:00', '15:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.15 36.81, 127.02 37.54)', 4326)),

              -- ⑫ 임봉사: 광주→전북 [독립, 매칭 적음]
              (:v12, NULL, '광주에서 전주까지 대중교통',
               '광주광역시', '전라북도', :dt, '07:00', '09:30', false, 'small', 'available',
               ST_GeomFromText('LINESTRING(126.85 35.16, 127.15 35.82)', 4326)),

              -- ⑬ 한릴레이: 전북→충남 [독립]
              (:v13, NULL, '전주에서 천안까지 차량',
               '전라북도', '충청남도', :dt, '10:00', '13:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.15 35.82, 127.15 36.81)', 4326)),

              -- ⑭ 조서울: 충남→인천 [독립]
              (:v14, NULL, '천안에서 인천까지 차량',
               '충청남도', '인천광역시', :dt, '14:00', '17:00', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.15 36.81, 126.70 37.45)', 4326)),

              -- ⑮ 송봉사: 경기→인천 [독립]
              (:v15, NULL, '수원에서 인천까지 차량',
               '경기도', '인천광역시', :dt, '14:00', '16:00', true, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.01 37.26, 126.70 37.45)', 4326)),

              -- ⑯ 권도움: 부산→경남 [독립, 매칭 범위 밖]
              (:v16, NULL, '부산에서 창원까지 차량',
               '부산광역시', '경상남도', :dt, '08:00', '10:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(129.07 35.18, 128.68 35.23)', 4326)),

              -- ⑰ 민릴레이: 대구→충북 [독립]
              (:v17, NULL, '대구에서 청주까지 차량',
               '대구광역시', '충청북도', :dt, '10:00', '13:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(128.60 35.87, 127.49 36.64)', 4326)),

              -- ⑱ 유봉사: 충북→경기 [독립]
              (:v18, NULL, '청주에서 수원까지 차량',
               '충청북도', '경기도', :dt, '14:00', '17:00', true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.49 36.64, 127.01 37.26)', 4326)),

              -- ⑲ 나릴레이: 경기→서울 대중교통 [독립]
              (:v19, NULL, '수원에서 서울까지 대중교통',
               '경기도', '서울특별시', :dt, '13:00', '15:00', false, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.01 37.26, 127.02 37.54)', 4326)),

              -- ⑳ 강서울: 대전→서울 직행 [독립]
              (:v20, NULL, '대전에서 서울까지 차량 직행',
               '대전광역시', '서울특별시', :dt, '09:00', '14:00', true, 'large', 'available',
               ST_GeomFromText('LINESTRING(127.39 36.35, 127.02 37.54)', 4326))
        """), {
            "v1": vols[0].id, "v2": vols[1].id, "v3": vols[2].id,
            "v4": vols[3].id, "v5": vols[4].id, "v6": vols[5].id,
            "v7": vols[6].id, "v8": vols[7].id, "v9": vols[8].id,
            "v10": vols[9].id, "v11": vols[10].id, "v12": vols[11].id,
            "v13": vols[12].id, "v14": vols[13].id, "v15": vols[14].id,
            "v16": vols[15].id, "v17": vols[16].id, "v18": vols[17].id,
            "v19": vols[18].id, "v20": vols[19].id,
            "p_choco": p_choco.id, "p_bboppi": p_bboppi.id,
            "p_luna": p_luna.id, "p_mongyi": p_mongyi.id, "p_kkami": p_kkami.id,
            "dt": DEMO_DATE,
        })

        await db.commit()

    # ── 완료 출력 ──────────────────────────────────────────────────────────────
    print()
    print("[완료] 시드 데이터 생성 완료")
    print()
    print("── 계정 ──────────────────────────────────────────────")
    print("  admin           : admin@pawrelay.com  / Admin1234!")
    print("  보호소 1 (광주) : shelter1@test.com  / Shelter1!")
    print("  보호소 2 (부산) : shelter2@test.com  / Shelter2!")
    print("  보호소 3 (전주) : shelter3@test.com  / Shelter3!")
    print("  보호소 4 (대전) : shelter4@test.com  / Shelter4!")
    for i, name in enumerate(VOL_NAMES, 1):
        direct = " ← 직접지원" if i in (1, 4, 5, 7, 10) else ""
        print(f"  봉사자 {i:2d} {name:6s} : vol{i}@test.com / Vol{i:02d}11!{direct}")
    print()
    print("── 예상 매칭 체인 ────────────────────────────────────")
    print("  초코 (광주→서울) : 김봉사 → 이릴레이 → 박서울")
    print("  뽀삐 (부산→대구) : 최자원 (단일 구간)")
    print("  루나 (부산→서울) : 정봉사 → 홍길동")
    print("  몽이 (전주→고양) : 황봉사 → 윤릴레이")
    print("  까미 (대전→서울) : 오릴레이 → 장도움")
    print()
    print("── 테스트 순서 ───────────────────────────────────────")
    print("  1. POST /auth/login              { admin@pawrelay.com / Admin1234! }")
    print("  2. POST /matching/run            (admin 토큰)")
    print("  3. GET  /shelter/dashboard       (각 보호소 토큰)")
    print("  4. PATCH /matching/relay-chains/{id}/approve  (보호소 승인)")
    print("  5. POST  /matching/accept/{id}   (봉사자 수락)")
    print("  6. POST  /matching/decline/{id}  (봉사자 거절 → backup promote 자동)")


if __name__ == "__main__":
    asyncio.run(seed())
