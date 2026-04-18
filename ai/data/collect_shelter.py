"""
공공데이터포털 APMS API 수집 스크립트
- 전국 지자체 동물보호소 위치·연락처 수집

실행:
    python -m ai.data.collect_shelter --output data/shelter.json
"""

import argparse
import asyncio
import json
import logging
import os
from typing import Optional

import httpx

from ai.models.waypoint import WaypointModel, WaypointType
from ai.utils.phone import normalize_phone

logger = logging.getLogger(__name__)

_SHELTER_URL = "https://apis.data.go.kr/1543061/animalShelterSrvc_v2/shelterInfo_v2"

_PAGE_SIZE = 1000
_TIMEOUT_SECONDS = 30


async def _fetch_json(
    client: httpx.AsyncClient,
    url: str,
    params: dict,
) -> dict:
    """단일 HTTP GET 요청을 보내고 JSON 응답을 반환."""
    response = await client.get(url, params=params, timeout=_TIMEOUT_SECONDS)
    response.raise_for_status()
    return response.json()


def _build_params(service_key: str, page: int) -> dict:
    """API 요청 파라미터 생성."""
    return {
        "serviceKey": service_key,
        "numOfRows": _PAGE_SIZE,
        "pageNo": page,
        "_type": "json",
    }


def _extract_items(body: dict) -> list[dict]:
    """응답 body에서 item 리스트 추출."""
    items = body.get("items", {})
    if not items:
        return []
    item_list = items.get("item", [])
    if isinstance(item_list, dict):
        item_list = [item_list]
    return item_list


async def _fetch_all_pages(
    client: httpx.AsyncClient,
    service_key: str,
) -> list[dict]:
    """페이지네이션을 처리해 전체 보호소 목록 반환."""
    results = []
    page = 1

    while True:
        params = _build_params(service_key, page)
        data = await _fetch_json(client, _SHELTER_URL, params)
        body = data.get("response", {}).get("body", {})
        total_count = int(body.get("totalCount") or 0)
        item_list = _extract_items(body)
        if not item_list:
            break
        results.extend(item_list)
        if total_count > 0 and len(results) >= total_count:
            break
        page += 1

    return results


def _parse_shelter(item: dict) -> Optional[WaypointModel]:
    """APMS 보호소 항목을 WaypointModel로 변환. 좌표 없거나 오류 시 None 반환."""
    try:
        lat = item.get("lat") if item.get("lat") is not None else item.get("latitude")
        lng = item.get("lng") if item.get("lng") is not None else item.get("longitude")

        if lat is None or lng is None:
            return None

        return WaypointModel(
            name=item["careNm"],
            type=WaypointType.SHELTER,
            latitude=float(lat),
            longitude=float(lng),
            address=item.get("careAddr"),
            phone=normalize_phone(item.get("careTel")),
            source="공공데이터포털_APMS_보호소API",
        )
    except (KeyError, ValueError, TypeError):
        return None


async def collect_shelters(service_key: str) -> list[WaypointModel]:
    """전국 동물보호소 전체 수집."""
    async with httpx.AsyncClient() as client:
        items = await _fetch_all_pages(client, service_key)

    results = [_parse_shelter(i) for i in items]
    valid = [r for r in results if r is not None]
    skipped = len(items) - len(valid)

    if skipped:
        logger.warning("파싱 실패 또는 좌표 없음으로 제외된 항목: %d건", skipped)

    return valid


async def _main():
    """CLI 진입점: 보호소 수집 후 JSON 파일로 저장."""
    logging.basicConfig(level=logging.INFO)

    service_key = os.environ.get("PUBLIC_DATA_API_KEY")
    if not service_key:
        raise ValueError("PUBLIC_DATA_API_KEY 환경변수를 설정해주세요.")

    parser = argparse.ArgumentParser(description="APMS 보호소 waypoints 수집")
    parser.add_argument("--output", default=None, help="저장할 JSON 파일 경로")
    args = parser.parse_args()

    shelters = await collect_shelters(service_key)
    logger.info("보호소: %d건", len(shelters))

    if args.output:
        output_data = {"shelter": [s.model_dump() for s in shelters]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info("저장 완료: %s", args.output)


if __name__ == "__main__":
    asyncio.run(_main())
