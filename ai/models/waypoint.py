from enum import Enum


class WaypointType(str, Enum):
    """인계 거점 유형."""
    REST_AREA = "rest_area"
    TRAIN = "train"
    BUS = "bus"
    SHELTER = "shelter"


# 데이터 모델 및 스키마 정의

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
    """

    def __init__(self, name, waypoint_type, latitude, longitude,
                 address=None, phone=None, source=None):
        if not (-90 <= latitude <= 90):
            raise ValueError(f"위도 범위 초과: {latitude} (허용: -90 ~ 90)")
        if not (-180 <= longitude <= 180):
            raise ValueError(f"경도 범위 초과: {longitude} (허용: -180 ~ 180)")

        self.name = name
        self.type = WaypointType(waypoint_type)
        self.address = address
        self.phone = phone
        self.latitude = latitude
        self.longitude = longitude
        self.source = source

    def to_dict(self):
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
        return {
            "name": self.name,
            "type": self.type.value,
            "address": self.address,
            "phone": self.phone,
            "geom": f"SRID=4326;POINT({self.longitude} {self.latitude})",
            "source": self.source,
        }


API_SOURCE_MAP = {
    "rest_area": "공공데이터포털_휴게소API",
    "train": "공공데이터포털_기차역API",
    "bus": "공공데이터포털_버스터미널API",
    "shelter": "공공데이터포털_APMS_보호소API",
}