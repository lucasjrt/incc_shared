import re
from datetime import datetime, timezone

ULID_RE = re.compile(r"^[0-9A-HJKMNP-TV-Z]{26}$")
COGNITO_SUB_RE = re.compile(r"^[A-Za-z0-9\-_:]{1,128}$")
FEATURE_RE = re.compile(r"^[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+(?::[a-zA-Z0-9_\-]+)+$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def is_valid_ulid(v: str) -> bool:
    return ULID_RE.match(v) is not None
