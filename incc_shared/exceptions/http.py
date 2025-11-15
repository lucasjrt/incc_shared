class HttpException(Exception):
    pass


class BadRequest(HttpException):
    pass


class Conflict(HttpException):
    pass


class Forbidden(HttpException):
    pass


class NotFound(HttpException):
    pass


class ServerError(HttpException):
    pass


class Unauthorized(HttpException):
    pass
