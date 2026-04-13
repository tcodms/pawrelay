import resend

from app.core.config import settings


def _configure() -> None:
    resend.api_key = settings.resend_api_key


async def send_verification_email(to: str, token: str) -> None:
    # TODO: 배포 시 이 분기 제거하고 Resend 도메인 인증 후 실제 발송으로 교체
    # 현재 로컬(development) 환경에서는 이메일 발송을 스킵함
    if settings.environment == "development":
        return

    _configure()
    verify_url = f"{settings.frontend_url}/auth/verify-email?token={token}"
    resend.Emails.send({
        "from": settings.email_from,
        "to": to,
        "subject": "[PawRelay] 이메일 인증을 완료해주세요",
        "html": (
            f"<p>아래 링크를 클릭해 이메일 인증을 완료해주세요.</p>"
            f"<p><a href='{verify_url}'>{verify_url}</a></p>"
            f"<p>링크는 24시간 동안 유효합니다.</p>"
        ),
    })
