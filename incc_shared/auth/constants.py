import os

COGNITO_REGION = os.environ.get("COGNITO_REGION", "sa-east-1")


def get_cognito_pool_id() -> str:
    try:
        return os.environ["COGNITO_POOL_ID"]
    except KeyError:
        raise RuntimeError("COGNITO_POOL_ID not set")


def get_cognito_client_id() -> str:
    try:
        return os.environ["COGNITO_CLIENT_ID"]
    except KeyError:
        raise RuntimeError("COGNITO_CLIENT_ID not set")
