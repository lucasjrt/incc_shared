import json
import traceback
from functools import wraps

from pydantic import ValidationError

from incc_shared.exceptions.errors import AppError, InvalidState
from incc_shared.exceptions.http import BadRequest, Forbidden, Unauthorized
from incc_shared.handler.http import create_response


def handler(model=None):
    def decorator(func):
        @wraps(func)
        def wrapper(event, context, *args, **kwargs):
            try:
                if not model:
                    return func(event, context, *args, **kwargs)

                try:
                    body = json.loads(event["body"])
                    if not body:
                        raise BadRequest("[handler] Missing request body")
                except json.JSONDecodeError as e:
                    raise BadRequest(f"[handler] Failed to decode json: {e}")

                try:
                    parsed = model(**body)
                except ValidationError as e:
                    for err in e.errors():
                        print(f"- {json.dumps(err, indent=2)}")
                    raise BadRequest("[handler] Failed to validate model")
                return func(event, context, model=parsed, *args, **kwargs)
            except InvalidState as e:
                print("Invalid state found:", e)
                # TODO: Add an sns alert for when this happens
                return create_response({"error": "Server Error"}, status_code=500)
            except AppError as e:
                print(e)
                return create_response(
                    {"error": e.code, "message": e.message}, status_code=400
                )
            except BadRequest as e:
                print(e)
                return create_response({"error": "Bad request"}, status_code=400)
            except Unauthorized:
                return create_response({"error": "Unauthorized"}, status_code=401)
            except Forbidden:
                return create_response({"error": "Forbidden"}, status_code=403)
            except Exception as e:
                traceback.print_exc()
                print("An exception happened when processing the request")
                print(e)
                return create_response({"error": "Server Error"}, status_code=500)

        return wrapper

    return decorator
