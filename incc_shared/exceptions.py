class BadRequest(Exception):
    pass


class Forbidden(Exception):
    pass


class ServerError(Exception):
    pass


class Unauthorized(Exception):
    pass


class InvalidState(ServerError):
    pass
