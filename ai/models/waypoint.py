from enum import Enum


class WaypointType(str, Enum):
    """인계 거점 유형."""
    REST_AREA = "rest_area"   # 휴게소
    TRAIN = "train"           # 기차역
    BUS = "bus"               # 버스터미널
    SHELTER = "shelter"       # 지자체 보호소


# SQLAlchemy 모델 (DB 연결 시 사용)
# PostGIS 확장 필요: CREATE EXTENSION postgis;

WAYPOINT_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS waypoints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    type VARCHAR(20) NOT NULL CHECK (type IN ('rest_area', 'train', 'bus', 'shelter')),
    address TEXT,
    phone VARCHAR(20),
    geom GEOMETRY(Point, 4326) NOT NULL,
    source VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_waypoints_type ON waypoints(type);
CREATE INDEX IF NOT EXISTS idx_waypoints_geom ON waypoints USING GIST(geom);
"""


class WaypointModel:
    """waypoints 테이블 데이터 구조.

    공공데이터포털 API에서 수집한 데이터를 이 형식으로 변환하여 저장한다.

    Attributes:
        name: 거점 이름 (예: "천안아산역", "천안휴게소")
        type: 거점 유형 (rest_area | train | bus | shelter)
        address: 주소
        phone: 연락처 (보호소만 해당)
        latitude: 위도
        longitude: 경도
        source: 데이터 출처 (예: "공공데이터포털_교통API")
    """

    def __init__(self, name, waypoint_type, latitude, longitude,
                 address=None, phone=None, source=None):
        self.name = name
        self.type = WaypointType(waypoint_type)
        self.address = address
        self.phone = phone
        self.latitude = latitude
        self.longitude = longitude
        self.source = source

    def to_dict(self):
        """API 응답 또는 DB 저장용 딕셔너리 반환."""
        return {
            "name": self.name,
            "type": self.type.value,
            "address": self.address,
            "phone": self.phone,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "source": self.source,
        }

    def to_postgis_insert(self):
        """PostGIS INSERT 쿼리 파라미터 반환."""
        return {
            "name": self.name,
            "type": self.type.value,
            "address": self.address,
            "phone": self.phone,
            "geom": f"SRID=4326;POINT({self.longitude} {self.latitude})",
            "source": self.source,
        }


# 공공데이터포털 API → WaypointModel 변환 매핑
API_SOURCE_MAP = {
    "rest_area": "공공데이터포털_휴게소API",
    "train": "공공데이터포털_기차역API",
    "bus": "공공데이터포털_버스터미널API",
    "shelter": "공공데이터포털_APMS_보호소API",
}