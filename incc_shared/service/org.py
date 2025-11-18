from typing import Any

from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.organization import OrganizationModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service import (
    create_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    update_dynamo_item,
)


def get_org(orgId: str):
    key = get_dynamo_key(orgId, EntityType.organization, orgId)
    return get_dynamo_item(key, OrganizationModel)


def create_organization():
    orgId = str(ULID())
    org_attr: dict[str, Any] = {"orgId": orgId}
    organization = OrganizationModel(**org_attr)
    create_dynamo_item(organization.to_item())
    return orgId


def update_organization(orgId: str, patch: UpdateOrganizationModel):
    key = get_dynamo_key(orgId, EntityType.organization, orgId)
    update_dynamo_item(key, patch.model_dump())
