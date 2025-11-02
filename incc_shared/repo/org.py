import os
from typing import Any, cast

import boto3
from boto3.dynamodb.conditions import Key

from incc_shared.exceptions import ServerError

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
