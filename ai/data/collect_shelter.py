"""
공공데이터포털 APMS API 수집 스크립트
- 전국 지자체 동물보호소 위치·연락처 수집

실행:
    python -m ai.data.collect_shelter --output data/shelter.json
"""

import argparse
import asyncio
import json
import os
from typing import Optional

import httpx

from ai.models.waypoint import WaypointModel, WaypointType

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


async def _fetch_all_pages(
    client: httpx.AsyncClient,
    service_key: str,
) -> list[dict]:
    """페이지네이션을 처리해 전체 보호소 목록 반환."""
    results = []
    page = 1

    while True:
        params = {
            "serviceKey": service_key,
            "numOfRows": _PAGE_SIZE,
            "pageNo": page,
            "_type": "json",
        }
        data = await _fetch_json(client, _SHELTER_URL, params)

        body = data.get("response", {}).get("body", {})
        total_count = int(body.get("totalCount", 0))
        items = body.get("items", {})

        if not items:
            break

        item_list = items.get("item", [])
        if isinstance(item_list, dict):
            item_list = [item_list]

        if not item_list:
            break

        results.extend(item_list)

        if len(results) >= total_count:
            break

        page += 1

    return results


def _parse_shelter(item: dict) -> Optional[WaypointModel]:
    """APMS 보호소 항목을 WaypointModel로 변환.

    APMS API 주요 필드:
        careNm      — 보호소명
        careAddr    — 주소
        careTel     — 전화번호
        lat         — 위도
        lng         — 경도
    """
    try:
        lat = item.get("lat") or item.get("latitude")
        lng = item.get("lng") or item.get("longitude")

        if not lat or not lng:
            return None

        return WaypointModel(
            name=item["careNm"],
            type=WaypointType.SHELTER,
            latitude=float(lat),
            longitude=float(lng),
            address=item.get("careAddr"),
            phone=_normalize_phone(item.get("careTel")),
            source="공공데이터포털_APMS_보호소API",
        )
    except (KeyError, ValueError, TypeError):
        return None


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


async def collect_shelters(service_key: str) -> list[WaypointModel]:
    """전국 동물보호소 전체 수집."""
    async with httpx.AsyncClient() as client:
        items = await _fetch_all_pages(client, service_key)

    results = [_parse_shelter(i) for i in items]
    valid = [r for r in results if r is not None]
    skipped = len(items) - len(valid)

    if skipped:
        print(f"[경고] 파싱 실패 또는 좌표 없음으로 제외된 항목: {skipped}건")

    return valid


async def _main():
    """CLI 진입점: 보호소 수집 후 JSON 파일로 저장."""
    parser = argparse.ArgumentParser(description="APMS 보호소 waypoints 수집")
    parser.add_argument("--output", default=None, help="저장할 JSON 파일 경로")
    args = parser.parse_args()

    service_key = os.environ.get("PUBLIC_DATA_API_KEY")
    if not service_key:
        raise ValueError("PUBLIC_DATA_API_KEY 환경변수를 설정해주세요.")

    shelters = await collect_shelters(service_key)
    print(f"보호소: {len(shelters)}건")

    if args.output:
        output_data = {"shelter": [s.model_dump() for s in shelters]}
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"저장 완료: {args.output}")


if __name__ == "__main__":
    asyncio.run(_main())
