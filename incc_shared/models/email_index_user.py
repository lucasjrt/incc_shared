from typing import List

from pydantic import BaseModel, ValidationError, field_validator

from incc_shared.models.user import Role


class EmailIndexUserModel(BaseModel):
    tenant: str
    entity: str
    roles: List[Role] = [Role.USER]
    features: List[str] = []
    orgId: str = ""

    gsi_email_pk: str
    gsi_user_sk: str

    @field_validator("orgId", mode="after")
    def validate_orgId(cls, v: str) -> str:
        if not v:
            try:
                return cls.tenant.split("#")[1]
            except IndexError:
                raise ValidationError("Tenant must be on format ORG#{ID}")
        return v
