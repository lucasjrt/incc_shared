import os
from functools import wraps

import boto3
import cognitojwt
from boto3.dynamodb.conditions import Key
from cognitojwt.exceptions import CognitoJWTException

from ..utils.http import create_response

COGNITO_REGION = os.environ["COGNITO_REGION"]
COGNITO_POOL_ID = os.environ["COGNITO_POOL_ID"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


class Unauthorized(Exception):
    pass


def required_permissions(*allowed_permissions, match="any"):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context, *args, **kwargs):
            try:
                # Auth token required
                headers = event["headers"]
                auth = headers.get("authorization", headers.get("Authorization"))
                if not headers:
                    print("Missing authorizaton header")
                    raise Unauthorized()

                # Token must be valid
                token = auth.split("Bearer ")[1]
                if not token:
                    print("Invalid token")
                    raise Unauthorized()

                # Token must be verified
                verified = cognitojwt.decode(
                    token,
                    COGNITO_REGION,
                    COGNITO_POOL_ID,
                    app_client_id=COGNITO_CLIENT_ID,
                )
                event["username"] = verified["username"]

                # User must exist in database (fully registered)
                event["user"] = get_user(event["username"])
                if not event["user"]:
                    print("User not fully registered")
                    raise Unauthorized()

                # User must have permission
                features = event["user"]["features"]
                if match == "all":
                    ok = all(p in features for p in allowed_permissions)
                elif match == "any":
                    ok = bool(features.intersection(allowed_permissions))
                else:
                    raise ValueError(f"Match type of {match} is not valid")

                if not ok:
                    print("Invalid permissions")
                    raise Unauthorized()

                # All good. User and username injected in context
                return func(event, context, *args, **kwargs)
            except (Unauthorized, IndexError, CognitoJWTException) as e:
                print("Failed to authenticate/authorize:", e)
                return create_response({"error": "Unauthorized"}, status_code=401)

        return wrapper

    return decorator


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
        raise ValueError(f"Duplicate user in database: {user_key}")
    elif response["Count"] == 0:
        print(f"User {user_key} not found in database. Complete registration required")
        return None

    user = response["Items"][0]
    return user
