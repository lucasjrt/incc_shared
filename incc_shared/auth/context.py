from contextlib import contextmanager
from contextvars import ContextVar

from ulid import ULID

from incc_shared.exceptions.errors import InvalidState, PermissionDenied
from incc_shared.models.db.indexes.user_index import UserIndexModel
from incc_shared.models.db.user.user import UserModel
from incc_shared.models.feature import Feature, Resource, Scope

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


@contextmanager
def impersonate(org_id: ULID):
    current = _current_actor.get()
    if current is None:
        print("Attempt to impersonate without a valid context")
        raise InvalidState("User expected but is not set")

    if not current.has_permission(Feature.write(Resource.org, scope=Scope.all)):
        print(f"User {current.entity} tried to impersonate without permission")
        raise PermissionDenied("User not allowed to impersonate org")

    impersonated = current.model_copy()
    impersonated.orgId = org_id
    impersonated.entity = f"{current.entity}#{current.orgId}"

    print(f"Impersonation authorized: {impersonated.entity}")

    prev = current
    set_context_entity(impersonated)

    try:
        yield
    finally:
        set_context_entity(prev)
