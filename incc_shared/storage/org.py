import os
from typing import Any, cast

import boto3
from boto3.dynamodb.conditions import Key

from incc_shared.exceptions import ServerError
from incc_shared.models.organization import Defaults

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


def get_org(orgId: str):
    org_key = f"ORG#{orgId}"
    query = table.query(
        KeyConditionExpression=Key("tenant").eq(org_key) & Key("entity").eq(org_key)
    )
    if len(query["Items"]) == 0:
        return None
    elif len(query["Items"]) > 1:
        raise ServerError("Invalid state: More than one org was found with same ID")
    org: dict[str, Any] = cast(dict[str, Any], query["Items"][0])
    return org


def update_org(orgId: str, items: Defaults):
    to_update = items.model_dump()
    tenant_key = f"ORG#{orgId}"
    key = {
        "tenant": tenant_key,
        "entity": tenant_key,
    }

    update_expr = "SET " + ", ".join(f"#{k} = :{k}" for k in to_update)
    expr_attr_values = {f":{k}": v for k, v in to_update.items()}
    expr_attr_names = {f"#{k}": k for k in to_update}
    table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_attr_names,
        ExpressionAttributeValues=expr_attr_values,
        ReturnValues="UPDATED_NEW",
    )

    print(f"Updated defaults for {orgId}")
