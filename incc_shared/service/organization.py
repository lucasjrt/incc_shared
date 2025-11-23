from botocore.exceptions import ClientError

from incc_shared.auth.context import get_context_entity
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.common import get_default_juros, get_default_multa
from incc_shared.models.db.organization import OrganizationModel
from incc_shared.models.db.organization.base import Defaults
from incc_shared.models.request.organization.org_setup import SetupOrgModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service.storage.dynamodb import (
    get_dynamo_item,
    get_dynamo_key,
    set_dynamo_item,
    update_dynamo_item,
)


def get_org():
    user = get_context_entity()
    key = get_dynamo_key(EntityType.organization, user.orgId)
    return get_dynamo_item(key, OrganizationModel)


def setup_organization(model: SetupOrgModel):
    org = get_org()
    if not org:
        raise InvalidState("Attempt to updated org that does not exist")

    if org.beneficiario:
        raise InvalidState("Organization already setup")

    org.beneficiario = model.beneficiario
    if model.defaults:
        org.defaults = model.defaults
    else:
        multa = get_default_multa()
        juros = get_default_juros()
        org.defaults = Defaults(multa=multa, juros=juros, comQrcode=False)

    set_dynamo_item(org.to_item())


def update_organization(patch: UpdateOrganizationModel):
    user = get_context_entity()
    key = get_dynamo_key(EntityType.organization, user.orgId)
    try:
        update_dynamo_item(key, patch.to_item())
    except ClientError as e:
        if e.response.get("Error", {}).get(
            "Code"
        ) == "ValidationException" and "The document path provided in the update expression is invalid" in e.response.get(
            "Error", {}
        ).get(
            "Message", ""
        ):
            raise InvalidState("Org must be setup first before update")
        raise
