from functools import cached_property
from typing import List

from pydantic import BaseModel, ValidationError, computed_field

from incc_shared.models.user import Role


class UserIndexUserModel(BaseModel):
    tenant: str
    entity: str
    roles: List[Role] = [Role.USER]
    features: List[str] = []

    gsi_user_pk: str
    gsi_org_sk: str

    @computed_field
    @cached_property
    def orgId(self) -> str:
        try:
            return self.tenant.split("#")[1]
        except IndexError:
            raise ValidationError("Tenant must be on format ORG#{ID}")
