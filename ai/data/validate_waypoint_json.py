import argparse
import json
import logging
from collections import Counter
from pathlib import Path

from pydantic import ValidationError

from ai.models.waypoint import WaypointModel

logger = logging.getLogger(__name__)


def _load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def _build_key(waypoint: WaypointModel) -> tuple[str, str]:
    return waypoint.name, waypoint.type.value


def _validate_record(path: Path, waypoint_type: str, index: int, record: dict) -> WaypointModel:
    try:
        return WaypointModel(**record)
    except ValidationError as exc:
        raise ValueError(
            f"{path}: invalid record #{index} in '{waypoint_type}'"
        ) from exc


def _add_record(
    path: Path,
    waypoint_type: str,
    index: int,
    record: dict,
    seen_keys: set[tuple[str, str]],
    counts: Counter,
) -> None:
    waypoint = _validate_record(path, waypoint_type, index, record)
    key = _build_key(waypoint)
    if key in seen_keys:
        raise ValueError(f"{path}: duplicated waypoint '{waypoint.name}' ({waypoint.type.value})")
    seen_keys.add(key)
    counts[waypoint.type.value] += 1


def _validate_records(
    path: Path, waypoint_type: str, records: list, seen_keys: set[tuple[str, str]], counts: Counter
) -> int:
    total = 0
    for index, record in enumerate(records, start=1):
        _add_record(path, waypoint_type, index, record, seen_keys, counts)
        total += 1
    return total


def _validate_file(path: Path) -> tuple[int, Counter]:
    data = _load_json(path)
    total = 0
    counts: Counter = Counter()
    seen_keys: set[tuple[str, str]] = set()
    for waypoint_type, records in data.items():
        if not isinstance(records, list):
            raise ValueError(f"{path}: '{waypoint_type}' must be a list")
        total += _validate_records(path, waypoint_type, records, seen_keys, counts)
    return total, counts


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate waypoint JSON seed files")
    parser.add_argument(
        "--file",
        action="append",
        required=True,
        help="Path to a waypoint JSON file. Repeat for multiple files.",
    )
    return parser


def _main() -> None:
    logging.basicConfig(level=logging.INFO)
    args = _build_parser().parse_args()

    grand_total = 0
    merged_counts: Counter = Counter()

    for file_arg in args.file:
        path = Path(file_arg)
        total, counts = _validate_file(path)
        grand_total += total
        merged_counts.update(counts)
        logger.info("%s: %d records %s", path, total, dict(counts))

    logger.info("validated total: %d records %s", grand_total, dict(merged_counts))


if __name__ == "__main__":
    _main()
