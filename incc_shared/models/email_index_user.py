from typing import List

from pydantic import BaseModel

from incc_shared.models.user import Role


class EmailIndexUserModel(BaseModel):
    tenant: str
    entity: str
    roles: List[Role] = [Role.USER]
    features: List[str] = []

    gsi_email_pk: str
    gsi_user_sk: str
