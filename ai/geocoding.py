"""
카카오 Geocoding API - 텍스트 주소를 위경도 좌표로 변환.

환경변수:
    KAKAO_REST_API_KEY: 카카오 REST API 키

사용:
    coords = await geocode("광주광역시")
    # → (35.15, 126.85) 또는 ValueError 발생
"""

import logging
import os

import httpx

logger = logging.getLogger(__name__)

_KAKAO_GEOCODE_URL = "https://dapi.kakao.com/v2/local/search/address.json"
_TIMEOUT_SECONDS = 10


def _get_api_key() -> str:
    """KAKAO_REST_API_KEY 환경변수 반환. 미설정 시 ValueError."""
    key = os.environ.get("KAKAO_REST_API_KEY")
    if not key:
        raise ValueError("KAKAO_REST_API_KEY 환경변수를 설정해주세요.")
    return key


def _parse_coords(data: dict) -> tuple[float, float] | None:
    """응답 JSON에서 (위도, 경도) 추출. 결과 없으면 None 반환."""
    documents = data.get("documents", [])
    if not documents:
        return None
    doc = documents[0]
    try:
        return float(doc["y"]), float(doc["x"])  # y=위도, x=경도
    except (KeyError, ValueError, TypeError):
        return None


async def _fetch_geocode(address: str, api_key: str) -> dict:
    """카카오 Geocoding API를 호출하고 응답 JSON을 반환한다."""
    headers = {"Authorization": f"KakaoAK {api_key}"}
    async with httpx.AsyncClient() as client:
        response = await client.get(
            _KAKAO_GEOCODE_URL,
            headers=headers,
            params={"query": address},
            timeout=_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        return response.json()


async def geocode(address: str) -> tuple[float, float]:
    """텍스트 주소를 (위도, 경도)로 변환한다. 실패 시 ValueError 발생."""
    try:
        data = await _fetch_geocode(address, _get_api_key())
    except httpx.HTTPError as e:
        logger.warning("카카오 Geocoding API 호출 실패: %s", e)
        raise ValueError("Geocoding API 호출 실패") from e
    coords = _parse_coords(data)
    if coords is None:
        raise ValueError("주소 변환 결과 없음")
    return coords
