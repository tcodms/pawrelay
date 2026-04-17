"""
전국휴게소정보표준데이터 JSON 파일 파서

전국휴게소정보표준데이터는 파일 데이터(파일 다운로드 방식)로,
공공데이터포털에서 다운로드한 JSON 파일을 파싱한다.

실행:
    python -m ai.data.collect_transport --file 경로/전국휴게소정보표준데이터.json
    python -m ai.data.collect_transport --file 경로/파일.json --output data/rest_area.json
"""

import argparse
import json
from typing import Optional

from ai.models.waypoint import WaypointModel, WaypointType


def _normalize_phone(raw: Optional[str]) -> Optional[str]:
    """전화번호를 0XX-XXX(X)-XXXX 형식으로 정규화."""
    if not raw:
        return None
    digits = "".join(c for c in raw if c.isdigit())
    if len(digits) == 9:
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 10:
        if digits.startswith("02"):
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return None


def _extract_field_keys(data: dict) -> tuple:
    keys = [field["id"] for field in data.get("fields", [])]
    if len(keys) < 7:
        raise ValueError(f"fields 개수 부족: {len(keys)}개 (최소 7개 필요)")
    phone_key = keys[25] if len(keys) > 25 else None
    return keys[0], keys[5], keys[6], phone_key


def _parse_record(
    record: dict,
    name_key: str,
    lat_key: str,
    lng_key: str,
    phone_key: Optional[str],
) -> Optional[WaypointModel]:
    raw_name = record[name_key]
    name = str(raw_name).strip() if raw_name is not None else ""
    if not name:
        return None
    return WaypointModel(
        name=name,
        type=WaypointType.REST_AREA,
        latitude=float(record[lat_key]),
        longitude=float(record[lng_key]),
        phone=_normalize_phone(record.get(phone_key)),
        source="공공데이터포털_전국휴게소정보표준데이터",
    )


def _parse_rest_area_records(
    records: list,
    name_key: str,
    lat_key: str,
    lng_key: str,
    phone_key: Optional[str],
) -> tuple[list[WaypointModel], int]:
    results = []
    skipped = 0
    for record in records:
        try:
            waypoint = _parse_record(record, name_key, lat_key, lng_key, phone_key)
            if waypoint:
                results.append(waypoint)
            else:
                skipped += 1
        except (KeyError, ValueError, TypeError):
            skipped += 1
    return results, skipped


def parse_rest_area_json(filepath: str) -> list[WaypointModel]:
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    name_key, lat_key, lng_key, phone_key = _extract_field_keys(data)
    results, skipped = _parse_rest_area_records(
        data.get("records", []), name_key, lat_key, lng_key, phone_key
    )
    if skipped:
        print(f"[경고] 파싱 실패로 제외된 항목: {skipped}건")
    return results


def _main():
    """CLI 진입점: 휴게소 JSON 파싱 후 저장."""
    parser = argparse.ArgumentParser(description="전국 휴게소 waypoints 파싱")
    parser.add_argument("--file", required=True, help="전국휴게소정보표준데이터.json 경로")
    parser.add_argument("--output", default=None, help="저장할 JSON 파일 경로")
    args = parser.parse_args()

    rest_areas = parse_rest_area_json(args.file)
    print(f"휴게소: {len(rest_areas)}건")

    if args.output:
        output_data = {"rest_area": [r.model_dump() for r in rest_areas]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {args.output}")


if __name__ == "__main__":
    _main()
