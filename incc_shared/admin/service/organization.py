from typing import Any, Optional

from ulid import ULID

from incc_shared.admin.storage import admin_create_dynamo_item
from incc_shared.models.db.organization.organization import OrganizationModel


def create_organization(org_id: Optional[ULID]):
    if not org_id:
        org_id = ULID()

    org_attr: dict[str, Any] = {"orgId": org_id}
    organization = OrganizationModel(**org_attr)
    admin_create_dynamo_item(organization.to_item())
    return org_id
