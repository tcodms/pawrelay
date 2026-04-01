from ai.models.waypoint import WaypointModel, WaypointType, API_SOURCE_MAP


def test_waypoint_creation():
    print("=== waypoint 생성 테스트 ===")

    waypoint = WaypointModel(
        name="천안아산역",
        waypoint_type="train",
        latitude=36.7946,
        longitude=127.1045,
        address="충남 천안시 동남구",
        source=API_SOURCE_MAP["train"],
    )

    assert waypoint.type == WaypointType.TRAIN
    print(f"이름: {waypoint.name}")
    print(f"타입: {waypoint.type.value}")
    print(f"dict: {waypoint.to_dict()}")

    print("=== waypoint 생성 테스트 성공 ===\n")


def test_shelter_with_phone():
    print("=== 보호소 waypoint 테스트 ===")

    shelter = WaypointModel(
        name="천안시 동물보호센터",
        waypoint_type="shelter",
        latitude=36.8151,
        longitude=127.1139,
        address="충남 천안시 서북구",
        phone="041-521-3000",
        source=API_SOURCE_MAP["shelter"],
    )

    assert shelter.type == WaypointType.SHELTER
    assert shelter.phone == "041-521-3000"
    print(f"보호소: {shelter.name}")
    print(f"연락처: {shelter.phone}")
    print(f"PostGIS: {shelter.to_postgis_insert()}")

    print("=== 보호소 waypoint 테스트 성공 ===\n")


def test_all_types():
    print("=== 전체 타입 테스트 ===")

    types = ["rest_area", "train", "bus", "shelter"]
    for t in types:
        w = WaypointModel(name=f"테스트_{t}", waypoint_type=t,
                          latitude=36.0, longitude=127.0)
        assert w.type.value == t
        print(f"  {t} ✓")

    print("=== 전체 타입 테스트 성공 ===\n")


if __name__ == "__main__":
    test_waypoint_creation()
    test_shelter_with_phone()
    test_all_types()
    print("모든 테스트 통과!")