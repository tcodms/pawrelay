import re
from enum import Enum
from typing import Optional

from pydantic import BaseModel, field_validator


class WaypointType(str, Enum):
    """인계 거점 유형."""
    REST_AREA = "rest_area"
    TRAIN = "train"
    BUS = "bus"
    SHELTER = "shelter"


# TODO: Alembic 마이그레이션으로 전환 필요
WAYPOINT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS waypoints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('rest_area', 'train', 'bus', 'shelter')),
    address TEXT,
    phone VARCHAR(20),
    geom GEOMETRY(Point, 4326) NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_waypoints_type ON waypoints(type);
CREATE INDEX IF NOT EXISTS idx_waypoints_geom ON waypoints USING GIST(geom);
"""


class WaypointModel(BaseModel):
    """waypoints 테이블 데이터 구조.

    공공데이터포털 API에서 수집한 데이터를 이 형식으로 변환하여 저장한다.
    """

    name: str
    type: WaypointType
    latitude: float
    longitude: float
    address: Optional[str] = None
    phone: Optional[str] = None
    source: Optional[str] = None

    @field_validator("latitude")
    @classmethod
    def validate_latitude(cls, v: float) -> float:
        """위도 범위(-90~90)를 검증한다."""
        if not (-90 <= v <= 90):
            raise ValueError(f"위도 범위 초과: {v} (허용: -90 ~ 90)")
        return v

    @field_validator("longitude")
    @classmethod
    def validate_longitude(cls, v: float) -> float:
        """경도 범위(-180~180)를 검증한다."""
        if not (-180 <= v <= 180):
            raise ValueError(f"경도 범위 초과: {v} (허용: -180 ~ 180)")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """한국 전화번호 형식을 검증한다."""
        if v is None:
            return v
        # 한국 전화번호: 02-XXXX-XXXX, 0XX-XXX-XXXX, 0XX-XXXX-XXXX
        if not re.match(r"^0\d{1,2}-\d{3,4}-\d{4}$", v):
            raise ValueError(f"전화번호 형식 오류: {v} (예: 041-521-3000)")
        return v

    def to_postgis_insert(self) -> dict:
        """INSERT용 파라미터 dict를 반환한다.

        반드시 파라미터화된 쿼리로 사용할 것:
            await conn.execute(
                "INSERT INTO waypoints (name, type, address, phone, geom, source) "
                "VALUES ($1, $2, $3, $4, ST_GeomFromEWKT($5), $6)",
                data["name"], data["type"], data["address"],
                data["phone"], data["geom"], data["source"]
            )
        절대 문자열 포매팅으로 SQL에 직접 삽입하지 말 것.
        """
        return {
            "name": self.name,
            "type": self.type.value,
            "address": self.address,
            "phone": self.phone,
            "geom": f"SRID=4326;POINT({self.longitude} {self.latitude})",
            "source": self.source,
        }


API_SOURCE_MAP = {
    "rest_area": {
        "name": "공공데이터포털_휴게소API",
        "url": "https://www.data.go.kr/data/15028454/openapi.do",
    },
    "train": {
        "name": "공공데이터포털_기차역API",
        "url": "https://www.data.go.kr/data/15067994/openapi.do",
    },
    "bus": {
        "name": "공공데이터포털_버스터미널API",
        "url": "https://www.data.go.kr/data/15067000/openapi.do",
    },
    "shelter": {
        "name": "공공데이터포털_APMS_보호소API",
        "url": "https://www.data.go.kr/data/15098931/openapi.do",
    },
}
