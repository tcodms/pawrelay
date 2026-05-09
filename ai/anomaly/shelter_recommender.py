import json
import os
from pathlib import Path

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
    address = row.get("address") or ""
    return any(region in address for region in activity_regions)


def _to_model(row):
    return RecommendedShelter(
        name=row["name"],
        address=row.get("address") or "",
        phone=row.get("phone"),
    )


def recommend_shelters(activity_regions, shelter_path=None, limit=3):
    rows = _load_rows(shelter_path)
    matched = [row for row in rows if _matches_region(row, activity_regions)]
    selected = matched or rows
    return [_to_model(row) for row in selected[:limit]]
