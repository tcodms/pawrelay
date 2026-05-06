from app.services.email_service import send_sos_alert


async def send_delayed_sos_alert(
    segment_id: int,
    volunteer_name: str,
    latitude: float | None,
    longitude: float | None,
) -> None:
    await send_sos_alert(segment_id, volunteer_name, latitude, longitude)
