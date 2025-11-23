import pytest

from incc_shared.auth.context import get_context_entity, impersonate, set_context_entity
from incc_shared.exceptions.errors import PermissionDenied
from incc_shared.models.request.user.create import CreateUserModel
from incc_shared.service.organization import get_org
from incc_shared.service.user import create_user, get_user, list_users


def test_user_lifecycle():
    test_email = "foo.bar@example.com"
    create_model = CreateUserModel(email=test_email)
    creator = get_context_entity()
    user_id = create_user(create_model)
    user = get_user(user_id)
    assert user
    assert user.email == test_email

    users = list_users()
    assert len(users) == 2
    found = False
    for u in users:
        if u.id == user_id:
            found = True
    assert found

    org = get_org()
    assert org

    try:
        set_context_entity(user)
        with pytest.raises(PermissionDenied):
            with impersonate(org.orgId):
                pass
    finally:
        set_context_entity(creator)

    # TODO: Update user
