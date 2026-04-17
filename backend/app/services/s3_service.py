import mimetypes
import uuid

from fastapi import HTTPException

from app.core.config import settings
from app.core.s3 import get_s3_client

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MIME_TO_EXT = {"image/jpeg": "jpg", "image/png": "png", "image/webp": "webp"}
EXT_TO_MIME = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}


def generate_upload_url(filename: str) -> tuple[str, str]:
    ext = ("." + filename.rsplit(".", 1)[-1].lower()) if "." in filename else ""
    mime_type = EXT_TO_MIME.get(ext) or mimetypes.guess_type(filename)[0]
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=400, detail={"error": "UNSUPPORTED_FILE_TYPE"})

    ext = MIME_TO_EXT[mime_type]
    key = f"animals/{uuid.uuid4()}.{ext}"

    s3 = get_s3_client()
    upload_url = s3.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.aws_s3_bucket,
            "Key": key,
            "ContentType": mime_type,
        },
        ExpiresIn=600,
    )
    photo_url = f"https://{settings.aws_s3_bucket}.s3.{settings.aws_region}.amazonaws.com/{key}"
    return upload_url, photo_url
