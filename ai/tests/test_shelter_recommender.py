import json

from ai.anomaly.shelter_recommender import recommend_shelters


def test_recommend_shelters_prefers_same_region(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["Chungcheongnam-do"], shelter_path=shelter_path)
    assert shelters[0].name == "Cheonan Shelter"


def test_recommend_shelters_falls_back_to_all(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["Jeju"], shelter_path=shelter_path)
    assert len(shelters) == 3


def _write_shelters(tmp_path):
    path = tmp_path / "shelter.json"
    payload = {"shelter": _sample_rows()}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _sample_rows():
    return [
        _row("Cheonan Shelter", "Chungcheongnam-do Cheonan"),
        _row("Suwon Shelter", "Gyeonggi-do Suwon"),
        _row("Daejeon Shelter", "Daejeon Yuseong-gu"),
    ]


def _row(name, address):
    return {"name": name, "address": address, "phone": "041-000-0000"}
