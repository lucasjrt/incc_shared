from typing import ClassVar, Optional

from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.organization.base import OrganizationBase


class OrganizationModel(OrganizationBase, DynamoBaseModel):
    ENTITY_TEMPLATE: ClassVar[Optional[str]] = "ORG#{orgId}"
