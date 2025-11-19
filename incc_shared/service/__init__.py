import base64
import os
from decimal import Decimal
from typing import Any, Type, TypeVar

import boto3
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from pydantic import BaseModel

from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import Conflict

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


def get_dynamo_key(orgId: str, entityType: EntityType, entityId: str):
    return {
        "tenant": f"ORG#{orgId}",
        "entity": f"{entityType.value}#{entityId}",
    }


def to_model(data: Any, model: Type[M]) -> M:
    return model.model_validate(normalize_item(data))


def get_dynamo_item(dynamo_key: dict, model: Type[M]):
    item = table.get_item(Key=dynamo_key).get("Item")
    if item:
        return to_model(item, model)

    return None


def _flatten_updates(
    prefix: tuple[str, ...],
    obj: Any,
    out: dict[tuple[str, ...], Any],
    exclude_none: bool = True,
):
    """
    Takes a dict and return a tuple to a value.
    Example
        {'a': {'b': 'c'}} -> {('a', 'b'): 'c'}
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten_updates(prefix + (k,), v, out)
    else:
        if exclude_none and obj is None:
            return
        out[prefix] = obj


def update_dynamo_item(key: dict, updates: dict):
    updates.pop("tenant", None)
    updates.pop("entity", None)

    flat: dict[tuple[str, ...], Any] = {}
    for k, v in updates.items():
        _flatten_updates((k,), v, flat)

    set_clauses = []
    expr_names = {}
    expr_vals = {}
    for i, (path_tuple, value) in enumerate(flat.items()):
        name_placeholders = []
        for j, seg in enumerate(path_tuple):
            ph = f"#n{i}_{j}"
            name_placeholders.append(ph)
            expr_names[ph] = seg
        path_expr = ".".join(name_placeholders)
        val_key = f":v{i}"
        set_clauses.append(f"{path_expr} = {val_key}")
        expr_vals[val_key] = value

    if not set_clauses:
        return None

    update_expr = "SET " + ", ".join(set_clauses)
    resp = table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_vals,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def create_dynamo_item(item: dict):
    tenant = item.get("tenant")
    if not tenant:
        raise ValueError("Item must have a tenant")

    entity = item.get("entity")
    if not entity:
        raise ValueError("Item must have an entity")

    try:
        table.put_item(
            Item=item,
            ConditionExpression=Attr(tenant).not_exists() & Attr(entity).not_exists(),
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise Conflict("Item already exists")
        else:
            error_message = e.response.get("Error", {}).get("Message")
            print(f"An unexpected error occurred: {error_code} - {error_message}")
            raise


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


def delete_dynamo_item(key: dict):
    table.delete_item(Key=key)


def list_dynamo_items(orgId: str, entityType: EntityType, model: Type[M]):
    org_key = f"ORG#{orgId}"
    entity_key = f"{entityType.value}#"
    response = table.query(
        KeyConditionExpression=Key("tenant").eq(org_key)
        & Key("entity").begins_with(entity_key),
    )

    if response.get("LastEvaluatedKey"):
        # TODO: SNS here, as it's not yet supported
        print("Pagination is expected, user data is now incomplete")

    return [to_model(c, model) for c in response["Items"]]
