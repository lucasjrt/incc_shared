import re
from datetime import datetime, timezone

COGNITO_SUB_RE = re.compile(r"^[A-Za-z0-9\-_:]{1,128}$")
FEATURE_RE = re.compile(r"^[a-zA-Z0-9_\-]+:[a-zA-Z0-9_\-]+(?::[a-zA-Z0-9_\-]+)*$")


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def regex_match(regex: str, word: str):
    return bool(re.fullmatch(regex, word))


def validate_entity(entity: str):
    entity_re = r"[A-Z]+#[A-Za-z0-9]+"
    return regex_match(entity_re, entity)
