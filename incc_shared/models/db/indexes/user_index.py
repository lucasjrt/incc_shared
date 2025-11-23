from functools import cached_property
from typing import List

from pydantic import ValidationError, computed_field

from incc_shared.models.db.user.base import Role
from incc_shared.models.feature import Feature, PermissionedEntity


class UserIndexModel(PermissionedEntity):
    tenant: str
    entity: str
    roles: List[Role] = [Role.user]

    gsi_user_pk: str
    gsi_org_sk: str

    @computed_field
    @cached_property
    def orgId(self) -> str:
        try:
            return self.tenant.split("#")[1]
        except IndexError:
            raise ValidationError("Tenant must be on format ORG#{ID}")
