import os
import traceback
from functools import wraps

import cognitojwt
from cognitojwt.exceptions import CognitoJWTException

from incc_shared.exceptions.http import Forbidden, Unauthorized
from incc_shared.handler.http import create_response
from incc_shared.storage.user import get_user_index_user

COGNITO_REGION = os.environ["COGNITO_REGION"]
COGNITO_POOL_ID = os.environ["COGNITO_POOL_ID"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]


def required_permissions(*allowed_permissions, match="any"):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context, *args, **kwargs):
            try:
                # Auth token required
                headers = event["headers"]
                auth = headers.get("authorization", headers.get("Authorization"))
                if not headers:
                    raise Unauthorized("Missing authorization header")

                # Token must be valid
                token = auth.split("Bearer ")[1]
                if not token:
                    raise Unauthorized("Ivalid token")

                # Token must be verified
                verified = cognitojwt.decode(
                    token,
                    COGNITO_REGION,
                    COGNITO_POOL_ID,
                    app_client_id=COGNITO_CLIENT_ID,
                )
                event["username"] = verified["username"]

                # User must exist in database (fully registered)
                user = get_user_index_user(event["username"])
                if not user:
                    print("User not fully registered")
                    raise Unauthorized()

                # User must have permission
                features = user.features
                if match == "all":
                    ok = all(p in features for p in allowed_permissions)
                elif match == "any":
                    feature_set = set(features)
                    permission_set = set(allowed_permissions)
                    ok = bool(feature_set & permission_set)
                else:
                    raise ValueError(f"Match type of {match} is not valid")

                if not ok:
                    raise Forbidden("Invalid permissions")

                event["user"] = user.model_dump()
                # All good. User and username injected in context
                return func(event, context, *args, **kwargs)
            except (
                AttributeError,
                Unauthorized,
                IndexError,
                CognitoJWTException,
                ValueError,
            ) as e:
                print("Failed to authenticate:", e)
            except Forbidden as e:
                print("Failed to authorize:", e)
                return create_response({"error": "Forbidden"}, status_code=403)
            except Exception as e:
                traceback.print_exc()
                print("Got an unexpected exception:", e)
            return create_response({"error": "Unauthorized"}, status_code=401)

        return wrapper

    return decorator
