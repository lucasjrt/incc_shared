from typing import Any, Optional

from ulid import ULID

from incc_shared.auth.context import impersonate
from incc_shared.models.db.organization.organization import OrganizationModel
from incc_shared.service.storage.dynamodb import create_dynamo_item


def create_organization(org_id: Optional[ULID]):
    if not org_id:
        org_id = ULID()

    org_attr: dict[str, Any] = {"orgId": org_id}
    organization = OrganizationModel(**org_attr)
    with impersonate(org_id):
        create_dynamo_item(organization.to_item())
    return org_id
