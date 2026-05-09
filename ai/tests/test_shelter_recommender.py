import json

from ai.anomaly.shelter_recommender import recommend_shelters


def test_recommend_shelters_prefers_same_region(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["충청남도"], shelter_path=shelter_path)
    assert shelters[0].name == "천안시 유기동물보호소"


def test_recommend_shelters_falls_back_to_all(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["제주특별자치도"], shelter_path=shelter_path)
    assert len(shelters) == 3


def _write_shelters(tmp_path):
    path = tmp_path / "shelter.json"
    payload = {"shelter": _sample_rows()}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _sample_rows():
    return [
        _row("천안시 유기동물보호소", "충청남도 천안시 동남구"),
        _row("수원시 유기동물보호소", "경기도 수원시 장안구"),
        _row("대전시 유기동물보호소", "대전광역시 유성구"),
    ]


def _row(name, address):
    return {"name": name, "address": address, "phone": "041-000-0000"}
