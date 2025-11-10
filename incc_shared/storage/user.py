import os

import boto3
from boto3.dynamodb.conditions import Key

from incc_shared.exceptions import InvalidState

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)


def get_user(username: str):
    user_key = f"USER#{username}"
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(DYNAMODB_TABLE)

    response = table.query(
        TableName=DYNAMODB_TABLE,
        IndexName="user_index",
        KeyConditionExpression=Key("gsi_user_pk").eq(user_key),
    )

    if response["Count"] > 1:
        print(f"User {user_key} is duplicate in database. It should never happen")
        print(f"Found {response['Count']} occurences in the database")
        raise InvalidState(f"Duplicate user in database: {user_key}")
    elif response["Count"] == 0:
        print(f"User {user_key} not found in database. Complete registration required")
        return None

    user = response["Items"][0]
    return user
