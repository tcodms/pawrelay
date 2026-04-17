"""전화번호 정규화 유틸리티."""

from typing import Optional


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    """전화번호를 0XX-XXX(X)-XXXX 형식으로 정규화."""
    if not raw:
        return None

    digits = "".join(c for c in str(raw) if c.isdigit())

    if digits.startswith("82"):
        digits = "0" + digits[2:]

    if not digits.startswith("0"):
        return None

    if len(digits) == 9 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 10:
        if digits.startswith("02"):
            return f"{digits[:2]}-{digits[2:6]}-{digits[6:]}"
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

    return None
