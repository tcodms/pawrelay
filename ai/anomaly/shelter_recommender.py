import json
import os
from pathlib import Path

from ai.anomaly.regions import find_region_in_text
from ai.anomaly.regions import normalize_regions
from ai.anomaly.schemas import RecommendedShelter


def _default_path():
    raw = os.getenv("SHELTER_DATA_PATH", "data/shelter.json")
    return Path(raw)


def _load_rows(shelter_path=None):
    path = Path(shelter_path) if shelter_path else _default_path()
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("shelter", data if isinstance(data, list) else [])


def _matches_region(row, activity_regions):
    row_region = find_region_in_text(row.get("address") or "")
    return row_region in activity_regions


def _to_model(row):
    return RecommendedShelter(
        name=row["name"],
        address=row.get("address") or "",
        phone=row.get("phone"),
    )


def recommend_shelters(activity_regions, shelter_path=None, limit=3):
    rows = _load_rows(shelter_path)
    regions = normalize_regions(activity_regions)
    if not regions:
        return []
    matched = [row for row in rows if _matches_region(row, regions)]
    selected = matched or rows
    return [_to_model(row) for row in selected[:limit]]
