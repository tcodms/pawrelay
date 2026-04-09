import pytest

from ai.models.waypoint import WaypointModel, WaypointType, API_SOURCE_MAP


def test_waypoint_creation():
    w = WaypointModel(
        name="천안아산역",
        type="train",
        latitude=36.7946,
        longitude=127.1045,
        address="충남 천안시 동남구",
        source=API_SOURCE_MAP["train"]["name"],
    )
    assert w.type == WaypointType.TRAIN
    assert w.latitude == 36.7946


def test_shelter_with_phone():
    shelter = WaypointModel(
        name="천안시 동물보호센터",
        type="shelter",
        latitude=36.8151,
        longitude=127.1139,
        phone="041-521-3000",
    )
    assert shelter.phone == "041-521-3000"
    postgis = shelter.to_postgis_insert()
    assert "POINT(127.1139 36.8151)" in postgis["geom"]


def test_invalid_latitude():
    with pytest.raises(Exception):
        WaypointModel(name="잘못된 위도", type="train", latitude=91.0, longitude=127.0)


def test_invalid_longitude():
    with pytest.raises(Exception):
        WaypointModel(name="잘못된 경도", type="train", latitude=36.0, longitude=181.0)


def test_invalid_phone_format():
    with pytest.raises(Exception):
        WaypointModel(name="잘못된 전화번호", type="shelter",
                      latitude=36.0, longitude=127.0, phone="010-1234-56789")


def test_all_waypoint_types():
    for t in ["rest_area", "train", "bus", "shelter"]:
        w = WaypointModel(name=f"테스트_{t}", type=t, latitude=36.0, longitude=127.0)
        assert w.type.value == t


def test_api_source_map_has_urls():
    for key, val in API_SOURCE_MAP.items():
        assert "name" in val
        assert "url" in val
        assert val["url"].startswith("http")
