"""
중간 발표용 목업 데이터 시드 스크립트

시나리오: 광주 → 서울 소형견 "초코" 3구간 릴레이
  1구간: 광주광역시 → 충청남도 (김봉사, 차량)
  2구간: 충청남도 → 경기도 (이릴레이, 대중교통)
  3구간: 경기도 → 서울특별시 (박서울, 차량)

실행:
  cd backend
  python seed_demo.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from datetime import date, datetime, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.core.security import hash_password
from app.models.user import User, ShelterProfile, VolunteerProfile
from app.models.post import TransportPost
from app.models.volunteer import VolunteerSchedule

DEMO_DATE = date(2026, 4, 27)

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


async def seed():
    async with AsyncSessionLocal() as db:
        existing = await db.execute(text("SELECT id FROM users WHERE email = 'admin@pawrelay.com'"))
        if existing.scalar_one_or_none():
            print("이미 시드 데이터가 존재합니다. 종료합니다.")
            return

        # ── 유저 생성 ────────────────────────────────────────────────
        admin = User(
            email="admin@pawrelay.com",
            password_hash=hash_password("Admin1234!"),
            name="관리자",
            role="admin",
            email_verified_at=datetime.now(tz=timezone.utc),
            account_status="active",
        )
        shelter_user = User(
            email="shelter@test.com",
            password_hash=hash_password("Shelter1!"),
            name="광주동물보호소",
            role="shelter",
            email_verified_at=datetime.now(tz=timezone.utc),
            account_status="active",
        )
        vol1 = User(
            email="vol1@test.com",
            password_hash=hash_password("Vol1111!"),
            name="김봉사",
            role="volunteer",
            email_verified_at=datetime.now(tz=timezone.utc),
            account_status="active",
        )
        vol2 = User(
            email="vol2@test.com",
            password_hash=hash_password("Vol2222!"),
            name="이릴레이",
            role="volunteer",
            email_verified_at=datetime.now(tz=timezone.utc),
            account_status="active",
        )
        vol3 = User(
            email="vol3@test.com",
            password_hash=hash_password("Vol3333!"),
            name="박서울",
            role="volunteer",
            email_verified_at=datetime.now(tz=timezone.utc),
            account_status="active",
        )

        db.add_all([admin, shelter_user, vol1, vol2, vol3])
        await db.flush()

        # ── 보호소 프로필 ─────────────────────────────────────────────
        shelter_profile = ShelterProfile(
            user_id=shelter_user.id,
            name="광주동물보호소",
            phone="062-000-0000",
            email="shelter@test.com",
            address="광주광역시 북구 운암동",
            verified_at=datetime.now(tz=timezone.utc),
        )

        # ── 봉사자 프로필 ─────────────────────────────────────────────
        vol1_profile = VolunteerProfile(
            user_id=vol1.id,
            vehicle_available=True,
            max_animal_size="small",
            activity_regions=["광주광역시", "충청남도"],
        )
        vol2_profile = VolunteerProfile(
            user_id=vol2.id,
            vehicle_available=False,
            max_animal_size="small",
            activity_regions=["충청남도", "경기도"],
        )
        vol3_profile = VolunteerProfile(
            user_id=vol3.id,
            vehicle_available=True,
            max_animal_size="medium",
            activity_regions=["경기도", "서울특별시"],
        )

        db.add_all([shelter_profile, vol1_profile, vol2_profile, vol3_profile])
        await db.flush()

        # ── 공고 ─────────────────────────────────────────────────────
        post = TransportPost(
            shelter_id=shelter_user.id,
            status="recruiting",
            animal_name="초코",
            animal_size="small",
            animal_notes="순한 편, 이동장 이용 가능",
            origin="광주광역시 북구 운암동",
            destination="서울특별시 강남구 역삼동",
            scheduled_date=DEMO_DATE,
        )

        db.add(post)
        await db.flush()

        # ── 봉사자 스케줄 (PostGIS LINESTRING 직접 삽입) ──────────────
        await db.execute(text("""
            INSERT INTO volunteer_schedules
              (volunteer_id, post_id, route_description,
               origin_area, destination_area,
               available_date, available_time, estimated_arrival_time,
               vehicle_available, max_animal_size, status, route)
            VALUES
              (:vid, NULL, '광주에서 천안까지 차량 이동',
               '광주광역시', '충청남도',
               :dt, '08:00', '12:00',
               true, 'small', 'available',
               ST_GeomFromText('LINESTRING(126.8526 35.1595, 127.1490 36.8151)', 4326)),

              (:vid2, NULL, '천안역에서 수원역까지 기차 이동',
               '충청남도', '경기도',
               :dt, '13:00', '16:00',
               false, 'small', 'available',
               ST_GeomFromText('LINESTRING(127.1490 36.8151, 127.0085 37.2636)', 4326)),

              (:vid3, NULL, '수원역에서 서울 강남까지 차량 이동',
               '경기도', '서울특별시',
               :dt, '17:00', '19:00',
               true, 'medium', 'available',
               ST_GeomFromText('LINESTRING(127.0085 37.2636, 127.0276 37.4979)', 4326))
        """), {"vid": vol1.id, "vid2": vol2.id, "vid3": vol3.id, "dt": DEMO_DATE})

        await db.commit()

        print("✅ 시드 데이터 생성 완료")
        print(f"   admin     : admin@pawrelay.com / Admin1234!")
        print(f"   보호소    : shelter@test.com / Shelter1!")
        print(f"   봉사자 1  : vol1@test.com / Vol1111!  (광주→충남, 차량)")
        print(f"   봉사자 2  : vol2@test.com / Vol2222!  (충남→경기, 대중교통)")
        print(f"   봉사자 3  : vol3@test.com / Vol3333!  (경기→서울, 차량)")
        print(f"   공고      : 초코 (소형견) 광주→서울, {DEMO_DATE}")
        print()
        print("다음 단계:")
        print("  1. POST /auth/login  { email: admin@pawrelay.com, password: Admin1234! }")
        print("  2. POST /matching/run  (admin 토큰)")
        print("  3. GET  /shelter/dashboard  (shelter 토큰)")
        print("  4. PATCH /matching/relay-chains/{chain_id}/approve  (shelter 토큰)")
        print("  5. PATCH /matching/relay-chains/{chain_id}/approve  (봉사자 토큰)")


if __name__ == "__main__":
    asyncio.run(seed())
