import traceback
from functools import wraps
from typing import List, Literal

import cognitojwt
from cognitojwt.exceptions import CognitoJWTException

from incc_shared.auth.constants import (
    COGNITO_REGION,
    get_cognito_client_id,
    get_cognito_pool_id,
)
from incc_shared.auth.context import set_context_entity
from incc_shared.exceptions.http import Forbidden, Unauthorized
from incc_shared.handler.http import create_response
from incc_shared.models.feature import Feature
from incc_shared.service.user import get_user_by_username


def required_permissions(
    feature_list: List[Feature], *, match: Literal["any", "all"] = "any"
):
    if match not in {"any", "all"}:
        raise ValueError(f"Match type of {match!r} is not valid")

    def decorator(func):
        @wraps(func)
        def wrapper(event, context, *args, **kwargs):
            try:
                # Auth token required
                headers = event.get("headers", {})
                auth = headers.get("authorization") or headers.get("Authorization")
                if not auth:
                    raise Unauthorized("Missing authorization header")

                # Token must be valid
                parts = auth.split("Bearer ")
                token = parts[1] if len(parts) == 2 else None
                if not token:
                    raise Unauthorized("Ivalid token")

                # Token must be verified
                verified = cognitojwt.decode(
                    token,
                    COGNITO_REGION,
                    get_cognito_pool_id(),
                    app_client_id=get_cognito_client_id(),
                )

                # User must exist in database (fully registered)
                user = get_user_by_username(verified["username"])
                if not user:
                    print("User not fully registered")
                    raise Unauthorized()

                # User must have permission
                if match == "all":
                    ok = all(user.has_permission(f) for f in feature_list)
                elif match == "any":
                    ok = any(user.has_permission(f) for f in feature_list)

                if not ok:
                    raise Forbidden("Invalid permissions")

                set_context_entity(user)

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
