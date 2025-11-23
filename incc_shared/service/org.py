from typing import Any, Optional

from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.organization import OrganizationModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service import (
    create_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    update_dynamo_item,
)


def get_org(org_id: ULID):
    key = get_dynamo_key(org_id, EntityType.organization, org_id)
    return get_dynamo_item(key, OrganizationModel)


def create_organization(org_id: Optional[ULID] = None):
    if not org_id:
        org_id = ULID()

    org_attr: dict[str, Any] = {"orgId": org_id}
    organization = OrganizationModel(**org_attr)
    create_dynamo_item(organization.to_item())
    return org_id


def update_organization(org_id: ULID, patch: UpdateOrganizationModel):
    key = get_dynamo_key(org_id, EntityType.organization, org_id)
    update_dynamo_item(key, patch.model_dump())
