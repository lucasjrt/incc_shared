import base64
import os
from decimal import Decimal
from typing import Any, Type, TypeVar

import boto3
from pydantic import BaseModel

M = TypeVar("M", bound=BaseModel)

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


def _normalize_value(v: Any) -> Any:
    if isinstance(v, Decimal):
        # prefer int when it's an integer-valued Decimal
        if v % 1 == 0:
            return int(v)
    if isinstance(v, bytes):
        # decode bytes (Dynamo can store binary). Choose base64 if arbitrary binary:
        try:
            return v.decode("utf-8")
        except Exception:
            return base64.b64encode(v).decode("ascii")
    if isinstance(v, set) or isinstance(v, list):
        return [_normalize_value(x) for x in v]
    if isinstance(v, dict):
        return {k: _normalize_value(val) for k, val in v.items()}
    return v


def normalize_item(item: dict) -> dict:
    return {k: _normalize_value(v) for k, v in item.items()}


def to_model(data: Any, model: Type[M]) -> M:
    return model.model_validate(normalize_item(data))
