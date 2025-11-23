from contextvars import ContextVar
from typing import Optional

from incc_shared.models.db.indexes.user_index import UserIndexModel
from incc_shared.models.db.user.user import UserModel

_current_actor: ContextVar[UserModel | UserIndexModel | None] = ContextVar(
    "entity", default=None
)


def set_context_entity(entity: UserModel | UserIndexModel):
    _current_actor.set(entity)


def get_context_entity() -> Optional[UserModel | UserIndexModel]:
    actor = _current_actor.get()
    return actor
