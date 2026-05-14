OFFICIAL_REGIONS = (
    "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
    "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
    "\ub300\uad6c\uad11\uc5ed\uc2dc",
    "\uc778\ucc9c\uad11\uc5ed\uc2dc",
    "\uad11\uc8fc\uad11\uc5ed\uc2dc",
    "\ub300\uc804\uad11\uc5ed\uc2dc",
    "\uc6b8\uc0b0\uad11\uc5ed\uc2dc",
    "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
    "\uacbd\uae30\ub3c4",
    "\uac15\uc6d0\ub3c4",
    "\ucda9\uccad\ubd81\ub3c4",
    "\ucda9\uccad\ub0a8\ub3c4",
    "\uc804\ub77c\ubd81\ub3c4",
    "\uc804\ub77c\ub0a8\ub3c4",
    "\uacbd\uc0c1\ubd81\ub3c4",
    "\uacbd\uc0c1\ub0a8\ub3c4",
    "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4",
)

_ALIASES = {
    "\uc11c\uc6b8": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
    "\uc11c\uc6b8\uc2dc": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
    "seoul": "\uc11c\uc6b8\ud2b9\ubcc4\uc2dc",
    "\ubd80\uc0b0": "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
    "\ubd80\uc0b0\uc2dc": "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
    "busan": "\ubd80\uc0b0\uad11\uc5ed\uc2dc",
    "\ub300\uad6c": "\ub300\uad6c\uad11\uc5ed\uc2dc",
    "\ub300\uad6c\uc2dc": "\ub300\uad6c\uad11\uc5ed\uc2dc",
    "daegu": "\ub300\uad6c\uad11\uc5ed\uc2dc",
    "\uc778\ucc9c": "\uc778\ucc9c\uad11\uc5ed\uc2dc",
    "\uc778\ucc9c\uc2dc": "\uc778\ucc9c\uad11\uc5ed\uc2dc",
    "incheon": "\uc778\ucc9c\uad11\uc5ed\uc2dc",
    "\uad11\uc8fc": "\uad11\uc8fc\uad11\uc5ed\uc2dc",
    "\uad11\uc8fc\uc2dc": "\uad11\uc8fc\uad11\uc5ed\uc2dc",
    "gwangju": "\uad11\uc8fc\uad11\uc5ed\uc2dc",
    "\ub300\uc804": "\ub300\uc804\uad11\uc5ed\uc2dc",
    "\ub300\uc804\uc2dc": "\ub300\uc804\uad11\uc5ed\uc2dc",
    "daejeon": "\ub300\uc804\uad11\uc5ed\uc2dc",
    "\uc6b8\uc0b0": "\uc6b8\uc0b0\uad11\uc5ed\uc2dc",
    "\uc6b8\uc0b0\uc2dc": "\uc6b8\uc0b0\uad11\uc5ed\uc2dc",
    "ulsan": "\uc6b8\uc0b0\uad11\uc5ed\uc2dc",
    "\uc138\uc885": "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
    "\uc138\uc885\uc2dc": "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
    "sejong": "\uc138\uc885\ud2b9\ubcc4\uc790\uce58\uc2dc",
    "\uacbd\uae30": "\uacbd\uae30\ub3c4",
    "gyeonggi": "\uacbd\uae30\ub3c4",
    "\uac15\uc6d0": "\uac15\uc6d0\ub3c4",
    "gangwon": "\uac15\uc6d0\ub3c4",
    "\ucda9\ubd81": "\ucda9\uccad\ubd81\ub3c4",
    "chungcheongbuk-do": "\ucda9\uccad\ubd81\ub3c4",
    "\ucda9\uccad\ubd81\ub3c4": "\ucda9\uccad\ubd81\ub3c4",
    "\ucda9\ub0a8": "\ucda9\uccad\ub0a8\ub3c4",
    "chungcheongnam-do": "\ucda9\uccad\ub0a8\ub3c4",
    "\ucda9\uccad\ub0a8\ub3c4": "\ucda9\uccad\ub0a8\ub3c4",
    "\uc804\ubd81": "\uc804\ub77c\ubd81\ub3c4",
    "jeollabuk-do": "\uc804\ub77c\ubd81\ub3c4",
    "\uc804\ub77c\ubd81\ub3c4": "\uc804\ub77c\ubd81\ub3c4",
    "\uc804\ub0a8": "\uc804\ub77c\ub0a8\ub3c4",
    "jeollanam-do": "\uc804\ub77c\ub0a8\ub3c4",
    "\uc804\ub77c\ub0a8\ub3c4": "\uc804\ub77c\ub0a8\ub3c4",
    "\uacbd\ubd81": "\uacbd\uc0c1\ubd81\ub3c4",
    "gyeongsangbuk-do": "\uacbd\uc0c1\ubd81\ub3c4",
    "\uacbd\uc0c1\ubd81\ub3c4": "\uacbd\uc0c1\ubd81\ub3c4",
    "\uacbd\ub0a8": "\uacbd\uc0c1\ub0a8\ub3c4",
    "gyeongsangnam-do": "\uacbd\uc0c1\ub0a8\ub3c4",
    "\uacbd\uc0c1\ub0a8\ub3c4": "\uacbd\uc0c1\ub0a8\ub3c4",
    "\uc81c\uc8fc": "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4",
    "\uc81c\uc8fc\uc2dc": "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4",
    "jeju": "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4",
    "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4": "\uc81c\uc8fc\ud2b9\ubcc4\uc790\uce58\ub3c4",
}


def normalize_region(region):
    raw = (region or "").strip()
    if raw in OFFICIAL_REGIONS:
        return raw
    return _ALIASES.get(raw.lower(), raw)


def normalize_regions(regions):
    seen = set()
    ordered = []
    for region in regions:
        normalized = normalize_region(region)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        ordered.append(normalized)
    return ordered


def find_region_in_text(text):
    raw = text or ""
    for official in OFFICIAL_REGIONS:
        if official in raw:
            return official
    for alias, official in _ALIASES.items():
        if alias in raw.lower():
            return official
    return ""
