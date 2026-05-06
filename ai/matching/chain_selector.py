import json
import logging

from ai.errors import notify_admin
from ai.providers import get_llm_provider

logger = logging.getLogger(__name__)

_MAX_RETRIES = 2
_REQUIRED_KEYS = {"chain", "backup_candidates", "matching_reason"}
_PROMPT_TEMPLATE = """You are selecting the best volunteer relay chain for an animal transport post.

Post:
{post}

Candidate chains:
{chains}

Rules:
- Return JSON only.
- "chain" must be exactly one candidate chain copied from the list above.
- "backup_candidates" must contain every remaining candidate chain, ordered by backup priority.
- Copy every segment object exactly, including schedule_id and volunteer_id.
- Prefer chains that include direct applicants when other quality factors are close.
- matching_reason must be 2-3 Korean sentences.

Return this schema exactly:
{{
  "chain": [{{"...": "..."}}],
  "backup_candidates": [
    [{{"...": "..."}}]
  ],
  "matching_reason": "..."
}}"""
_SEGMENT_KEYS = (
    "schedule_id",
    "volunteer_id",
    "origin_area",
    "destination_area",
    "available_date",
    "available_time",
    "estimated_arrival_time",
    "vehicle_available",
    "max_animal_size",
    "is_direct_apply",
)


def _build_prompt(chains: list[list[dict]], post: dict) -> str:
    post_json = json.dumps(post, ensure_ascii=False, indent=2)
    chains_json = json.dumps(chains, ensure_ascii=False, indent=2)
    return _PROMPT_TEMPLATE.format(post=post_json, chains=chains_json)


def _coerce_int(value):
    if type(value) is int:
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None


def _coerce_bool(value):
    if type(value) is bool:
        return value
    if not isinstance(value, str):
        return None
    lowered = value.strip().lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    return None


def _has_segment_keys(seg: dict) -> bool:
    missing = [key for key in _SEGMENT_KEYS if key not in seg]
    if not missing:
        return True
    logger.warning("segment missing keys: %s", ", ".join(missing))
    return False


def _normalize_segment_id(key: str, value) -> int | None:
    coerced = _coerce_int(value)
    if coerced is None:
        logger.warning("segment id type error for %s: %r", key, value)
    return coerced


def _normalize_segment_flag(key: str, value) -> bool | None:
    coerced = _coerce_bool(value)
    if coerced is None:
        logger.warning("segment bool type error for %s: %r", key, value)
    return coerced


def _normalize_segment_value(key: str, value):
    if key in {"schedule_id", "volunteer_id"}:
        return _normalize_segment_id(key, value)
    if key in {"vehicle_available", "is_direct_apply"}:
        return _normalize_segment_flag(key, value)
    if value is None:
        return None
    return str(value)


def _normalize_segment(seg: dict) -> dict | None:
    if not isinstance(seg, dict):
        logger.warning("segment type error: %r", type(seg))
        return None
    if not _has_segment_keys(seg):
        return None
    normalized = {}
    for key in _SEGMENT_KEYS:
        normalized[key] = _normalize_segment_value(key, seg[key])
        if normalized[key] is None and seg[key] is not None:
            return None
    return normalized


def _normalize_chain(chain: list[dict]) -> list[dict] | None:
    if not isinstance(chain, list) or not chain:
        logger.warning("chain type/empty error")
        return None
    normalized = []
    for seg in chain:
        normalized_seg = _normalize_segment(seg)
        if normalized_seg is None:
            return None
        normalized.append(normalized_seg)
    return normalized


def _chain_signature(chain: list[dict]) -> tuple:
    return tuple(tuple(seg[key] for key in _SEGMENT_KEYS) for seg in chain)


def _has_required_keys(data: dict) -> bool:
    if _REQUIRED_KEYS.issubset(data.keys()):
        return True
    logger.warning("response missing required keys: %s", data.keys())
    return False


def _has_matching_reason(data: dict) -> bool:
    reason = data["matching_reason"]
    if isinstance(reason, str) and reason.strip():
        return True
    logger.warning("matching_reason type/content error")
    return False


def _normalize_candidates(chains: list[list[dict]]) -> list[list[dict]] | None:
    normalized = []
    for candidate in chains:
        chain = _normalize_chain(candidate)
        if chain is None:
            logger.warning("input candidate chain is invalid")
            return None
        normalized.append(chain)
    return normalized


def _build_candidate_map(chains: list[list[dict]]) -> dict[tuple, list[dict]]:
    return {_chain_signature(candidate): candidate for candidate in chains}


def _validate_primary_chain(primary_data, candidate_map: dict[tuple, list[dict]]):
    primary_chain = _normalize_chain(primary_data)
    if primary_chain is None:
        logger.warning("primary chain is invalid")
        return None
    signature = _chain_signature(primary_chain)
    if signature not in candidate_map:
        logger.warning("primary chain not found in candidates")
        return None
    return signature, candidate_map[signature]


def _expected_backup_signatures(chains: list[list[dict]], primary_signature: tuple) -> list[tuple]:
    signatures = [_chain_signature(candidate) for candidate in chains]
    return [signature for signature in signatures if signature != primary_signature]


def _validate_backup_entry(backup, primary_signature: tuple, candidate_map: dict[tuple, list[dict]], seen: set):
    normalized = _normalize_chain(backup)
    if normalized is None:
        logger.warning("backup chain is invalid")
        return None
    signature = _chain_signature(normalized)
    if signature == primary_signature or signature not in candidate_map:
        logger.warning("backup chain not found in candidates")
        return None
    if signature in seen:
        logger.warning("duplicate backup chain returned")
        return None
    seen.add(signature)
    return signature, candidate_map[signature]


def _validate_backup_candidates(backups_data, primary_signature: tuple, candidate_map: dict[tuple, list[dict]], expected: list[tuple]):
    if not isinstance(backups_data, list):
        logger.warning("backup_candidates type error")
        return None
    backups = []
    seen = set()
    signatures = []
    for backup in backups_data:
        entry = _validate_backup_entry(backup, primary_signature, candidate_map, seen)
        if entry is None:
            return None
        signature, chain = entry
        signatures.append(signature)
        backups.append(chain)
    if len(signatures) != len(expected) or set(signatures) != set(expected):
        logger.warning("backup chain set mismatch")
        return None
    return backups


def _validate_fields(data: dict, chains: list[list[dict]]) -> dict | None:
    if not _has_required_keys(data) or not _has_matching_reason(data):
        return None
    normalized_candidates = _normalize_candidates(chains)
    if normalized_candidates is None:
        return None
    candidate_map = _build_candidate_map(normalized_candidates)
    primary = _validate_primary_chain(data["chain"], candidate_map)
    if primary is None:
        return None
    primary_signature, primary_chain = primary
    expected = _expected_backup_signatures(normalized_candidates, primary_signature)
    backups = _validate_backup_candidates(data["backup_candidates"], primary_signature, candidate_map, expected)
    if backups is None:
        return None
    return {"chain": primary_chain, "backup_candidates": backups, "matching_reason": data["matching_reason"].strip()}


def _strip_code_fence(text: str) -> str:
    return text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()


def _parse_response(text: str, chains: list[list[dict]]) -> dict | None:
    try:
        data = json.loads(_strip_code_fence(text))
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("JSON parse failed: %s", exc)
        return None
    if not isinstance(data, dict):
        logger.warning("response type error: expected dict")
        return None
    return _validate_fields(data, chains)


def _init_provider(post: dict):
    try:
        return get_llm_provider()
    except Exception as exc:
        error_msg = f"LLM provider init failed (post_id={post.get('id')}): {exc}"
        notify_admin(error_msg)
        raise ValueError(error_msg) from exc


async def _attempt_once(provider, prompt: str, chains: list[list[dict]]) -> dict | None:
    response = await provider.complete(prompt)
    return _parse_response(response, chains)


def _log_call_failure(attempt: int, exc: Exception) -> None:
    logger.warning("LLM call failed (%d/%d): %s", attempt + 1, _MAX_RETRIES + 1, exc)


def _log_validation_failure(attempt: int) -> None:
    logger.warning("LLM response validation failed (%d/%d)", attempt + 1, _MAX_RETRIES + 1)


async def _select_with_retries(provider, prompt: str, chains: list[list[dict]]) -> tuple[dict | None, Exception | None]:
    last_error = None
    for attempt in range(_MAX_RETRIES + 1):
        try:
            result = await _attempt_once(provider, prompt, chains)
        except Exception as exc:
            last_error = exc
            _log_call_failure(attempt, exc)
            continue
        if result is not None:
            return result, last_error
        _log_validation_failure(attempt)
    return None, last_error


def _handle_all_failed(post: dict, last_error: Exception | None) -> None:
    error_msg = f"LLM chain selection failed after {_MAX_RETRIES + 1} attempts (post_id={post.get('id')})"
    notify_admin(error_msg)
    if last_error is not None:
        raise ValueError(f"{error_msg} | last_error={last_error}") from last_error
    raise ValueError(error_msg)


def _validate_input_chains(chains: list[list[dict]]) -> None:
    if not chains:
        raise ValueError("candidate chains are empty")
    if any(not chain for chain in chains):
        raise ValueError("candidate chains contain an empty chain")


async def select_chain(chains: list[list[dict]], post: dict) -> dict:
    _validate_input_chains(chains)
    provider = _init_provider(post)
    prompt = _build_prompt(chains, post)
    result, last_error = await _select_with_retries(provider, prompt, chains)
    if result is not None:
        return result
    _handle_all_failed(post, last_error)
