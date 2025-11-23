from typing import List

from incc_shared.models.db.user.base import Role
from incc_shared.models.feature import PermissionedEntity


class UserIndexModel(PermissionedEntity):
    tenant: str
    entity: str
    roles: List[Role] = [Role.user]

    gsi_user_pk: str
    gsi_org_sk: str
