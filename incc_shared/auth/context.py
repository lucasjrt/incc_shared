from contextvars import ContextVar

from incc_shared.exceptions.errors import PermissionDenied
from incc_shared.models.db.indexes.user_index import UserIndexModel
from incc_shared.models.db.user.user import UserModel

_current_actor: ContextVar[UserModel | UserIndexModel | None] = ContextVar(
    "entity", default=None
)


def set_context_entity(entity: UserModel | UserIndexModel):
    _current_actor.set(entity)


def get_context_entity() -> UserModel | UserIndexModel:
    actor = _current_actor.get()
    if actor is None:
        raise PermissionDenied("User expected but is not set")
    return actor
