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


def update_dynamo_item(key: dict, data: dict):
    # Build expressions with dot-notation support
    update_expr_parts = []
    expr_attr_values = {}
    expr_attr_names = {}

    for k, v in data.items():
        path_parts = k.split(".")
        name_aliases = [f"#{p}" for p in path_parts]
        value_alias = f":{path_parts[-1]}"

        # Add to expression
        update_expr_parts.append(f"{'.'.join(name_aliases)} = {value_alias}")
        expr_attr_values[value_alias] = v

        # Add all the nested names
        for p, alias in zip(path_parts, name_aliases):
            expr_attr_names[alias] = p

    update_expr = "SET " + ", ".join(update_expr_parts)

    return table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="UPDATED_NEW",
    )


def patch_dict(whole: dict, to_patch: dict, ignore_nulls: bool = True):
    whole.update(
        {
            k: v
            for k, v in to_patch.items()
            if k in whole and (not ignore_nulls or v is not None)
        }
    )


def fill_dict(filling: dict, filler: dict):
    for key in filling:
        if key in filler:
            filling[key] = filler[key]
