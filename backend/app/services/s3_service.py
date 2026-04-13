import uuid

from app.core.config import settings
from app.core.s3 import get_s3_client


def generate_upload_url(filename: str) -> tuple[str, str]:
    ext = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
    key = f"animals/{uuid.uuid4()}.{ext}"

    s3 = get_s3_client()
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.aws_s3_bucket,
            "Key": key,
            "ContentType": "image/*",
        },
        ExpiresIn=600,
    )
    photo_url = f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
    return upload_url, photo_url
