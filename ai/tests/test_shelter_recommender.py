import json

from ai.anomaly.regions import normalize_region
from ai.anomaly.shelter_recommender import recommend_shelters


def test_recommend_shelters_prefers_same_region(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["\ucda9\ub0a8"], shelter_path=shelter_path)
    assert shelters[0].name == "\ucc9c\uc548\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c"


def test_recommend_shelters_falls_back_to_all(tmp_path):
    shelter_path = _write_shelters(tmp_path)
    shelters = recommend_shelters(["Jeju"], shelter_path=shelter_path)
    assert len(shelters) == 3


def test_normalize_region_maps_aliases():
    assert normalize_region("\ucda9\ub0a8") == "\ucda9\uccad\ub0a8\ub3c4"
    assert normalize_region("Chungcheongnam-do") == "\ucda9\uccad\ub0a8\ub3c4"


def _write_shelters(tmp_path):
    path = tmp_path / "shelter.json"
    payload = {"shelter": _sample_rows()}
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return path


def _sample_rows():
    return [
        _row("\ucc9c\uc548\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c", "\ucda9\uccad\ub0a8\ub3c4 \ucc9c\uc548\uc2dc \ub3d9\ub0a8\uad6c"),
        _row("\uc218\uc6d0\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c", "\uacbd\uae30\ub3c4 \uc218\uc6d0\uc2dc \uc7a5\uc548\uad6c"),
        _row("\ub300\uc804\uc2dc \uc720\uae30\ub3d9\ubb3c\ubcf4\ud638\uc18c", "\ub300\uc804\uad11\uc5ed\uc2dc \uc720\uc131\uad6c"),
    ]


def _row(name, address):
    return {"name": name, "address": address, "phone": "041-000-0000"}
