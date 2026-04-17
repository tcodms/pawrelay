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
import logging

from ai.models.waypoint import WaypointModel, WaypointType
from ai.utils.phone import normalize_phone

logger = logging.getLogger(__name__)


def _extract_field_keys(data: dict) -> dict:
    """JSON 데이터에서 필드 키 매핑을 추출한다. 필드 수 부족 시 ValueError."""
    field_keys = [field["id"] for field in data.get("fields", [])]
    if len(field_keys) < 7:
        raise ValueError(f"fields 개수 부족: {len(field_keys)}개 (최소 7개 필요)")
    return {
        "name": field_keys[0],
        "addr": field_keys[3],
        "lat": field_keys[5],
        "lng": field_keys[6],
        "phone": field_keys[25] if len(field_keys) > 25 else None,
    }


def _parse_record(record: dict, keys: dict) -> WaypointModel | None:
    """단일 휴게소 레코드를 WaypointModel로 변환한다. 오류 시 None 반환."""
    try:
        lat, lng = float(record[keys["lat"]]), float(record[keys["lng"]])
        raw_name = record[keys["name"]]
        if not raw_name or not str(raw_name).strip():
            return None
        return WaypointModel(
            name=str(raw_name).strip(), type=WaypointType.REST_AREA,
            latitude=lat, longitude=lng,
            address=str(record.get(keys["addr"], "") or "").strip() or None,
            phone=normalize_phone(record.get(keys["phone"])),
            source="공공데이터포털_전국휴게소정보표준데이터",
        )
    except (KeyError, ValueError, TypeError):
        return None


def parse_rest_area_json(filepath: str) -> list[WaypointModel]:
    """전국휴게소정보표준데이터 JSON 파일 파싱."""
    with open(filepath, encoding="utf-8") as f:
        data = json.load(f)
    keys = _extract_field_keys(data)
    results, skipped = [], 0
    for record in data.get("records", []):
        parsed = _parse_record(record, keys)
        if parsed is None:
            skipped += 1
        else:
            results.append(parsed)
    if skipped:
        logger.warning("파싱 실패로 제외된 항목: %d건", skipped)
    return results


def _main():
    """CLI 진입점: 휴게소 JSON 파싱 후 저장."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description="전국 휴게소 waypoints 파싱")
    parser.add_argument("--file", required=True, help="전국휴게소정보표준데이터.json 경로")
    parser.add_argument("--output", default=None, help="저장할 JSON 파일 경로")
    args = parser.parse_args()

    rest_areas = parse_rest_area_json(args.file)
    logger.info("휴게소: %d건", len(rest_areas))

    if args.output:
        output_data = {"rest_area": [r.model_dump() for r in rest_areas]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info("저장 완료: %s", args.output)


if __name__ == "__main__":
    _main()
