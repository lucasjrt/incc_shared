import json


def create_response(body=None, status_code=200, headers=None, isBase64Encoded=False):
    """Generate a Lambda Proxy response with CORS headers."""
    cors_headers = {
        # TODO: Improve CORS headers
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Authorization,Content-Type",
    }

    if headers:
        cors_headers.update(headers)

    payload = {
        "statusCode": status_code,
        "headers": cors_headers,
        "isBase64Encoded": isBase64Encoded,
    }

    if body:
        payload["body"] = (body if isBase64Encoded else json.dumps(body, default=str),)

    return payload
