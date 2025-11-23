from functools import cached_property
from typing import List

from pydantic import ValidationError, computed_field, field_validator

from incc_shared.models.db.user.base import Role
from incc_shared.models.feature import PermissionedEntity


class EmailIndexModel(PermissionedEntity):
    tenant: str
    entity: str
    roles: List[Role] = [Role.user]
    orgId: str = ""

    gsi_email_pk: str
    gsi_org_sk: str

    @field_validator("orgId", mode="after")
    def validate_orgId(cls, v: str) -> str:
        if not v:
            try:
                return cls.tenant.split("#")[1]
            except IndexError:
                raise ValidationError("Tenant must be on format ORG#{ID}")
        return v

    @computed_field
    @cached_property
    def id(self) -> str:
        try:
            return self.tenant.split("#")[1]
        except IndexError:
            raise ValidationError("Invalid tenant format")

    @computed_field
    @cached_property
    def email(self) -> str:
        try:
            return self.gsi_email_pk.split("#")[1]
        except IndexError:
            raise ValidationError("Invalid tenant format")
