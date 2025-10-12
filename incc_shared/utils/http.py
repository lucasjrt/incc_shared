import json


def create_response(body, status_code=200, headers=None):
    """Generate a Lambda Proxy response with CORS headers."""
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type",
    }
    if headers:
        cors_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": cors_headers,
        "body": json.dumps(body),
    }
