from boto3.dynamodb.conditions import Key

from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.db.indexes import UserIndexUserModel
from incc_shared.models.user import UserModel
from incc_shared.storage import table, to_model


def get_user(orgId: str, username: str):
    tenant_key = f"ORG#{orgId}"
    user_key = f"USER#{username}"

    response = table.get_item(Key={"tenant": tenant_key, "entity": user_key})

    user = response.get("Item")
    if not user:
        return None

    return to_model(user, UserModel)


def get_user_index_user(username: str):
    user_key = f"USER#{username}"

    response = table.query(
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
    return to_model(user, UserIndexUserModel)
