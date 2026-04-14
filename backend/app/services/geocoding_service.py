import httpx

from app.core.config import settings


async def geocode(address: str) -> tuple[float, float]:
    url = "https://dapi.kakao.com/v2/local/search/address.json"
    headers = {"Authorization": f"KakaoAK {settings.kakao_rest_api_key}"}
    params = {"query": address}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()

    documents = data.get("documents", [])
    if not documents:
        raise ValueError("GEOCODING_FAILED")

    longitude = float(documents[0]["x"])
    latitude = float(documents[0]["y"])
    return latitude, longitude
