"""전화번호 정규화 유틸리티."""

from typing import Optional


def _to_domestic_digits(raw: str) -> str:
    digits = "".join(c for c in str(raw) if c.isdigit())
    if digits.startswith("82"):
        digits = "0" + digits[2:]
    return digits


def _format_digits(digits: str) -> Optional[str]:
    if len(digits) == 9 and digits.startswith("02"):
        return f"{digits[:2]}-{digits[2:5]}-{digits[5:]}"
    if len(digits) == 10:
        sep = 2 if digits.startswith("02") else 3
        return f"{digits[:sep]}-{digits[sep:sep+4]}-{digits[sep+4:]}"
    if len(digits) == 11:
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
    return None


def normalize_phone(raw: Optional[str]) -> Optional[str]:
    if not raw:
        return None
    digits = _to_domestic_digits(raw)
    if not digits.startswith("0"):
        return None
    return _format_digits(digits)
