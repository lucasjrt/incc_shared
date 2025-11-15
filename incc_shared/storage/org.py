from boto3.dynamodb.conditions import Key

from incc_shared.exceptions.errors import InvalidData, InvalidState
from incc_shared.models.organization import OrganizationModel
from incc_shared.models.request.organization.patch import PatchOrgModel
from incc_shared.storage import patch_dict, table, to_model, update_dynamo_item


def get_org(orgId: str):
    org_key = f"ORG#{orgId}"
    query = table.query(
        KeyConditionExpression=Key("tenant").eq(org_key) & Key("entity").eq(org_key)
    )

    if len(query["Items"]) == 0:
        return None
    elif len(query["Items"]) > 1:
        raise InvalidState("More than one org was found with same ID")

    return to_model(query["Items"][0], OrganizationModel)


def update_org(orgId: str, patch: PatchOrgModel):
    tenant_key = f"ORG#{orgId}"
    key = {
        "tenant": tenant_key,
        "entity": tenant_key,
    }

    org = get_org(orgId)
    if not org:
        raise InvalidState("Org does not exist")

    org = org.to_item()

    item = {}
    if patch.beneficiario:
        beneficiario = org["beneficiario"]
        patch_dict(beneficiario, patch.beneficiario.model_dump())
        item["beneficiario"] = beneficiario

    if patch.defaults:
        defaults = org["defaults"]
        patch_dict(defaults, patch.defaults.model_dump())
        item["defaults"] = defaults

    if not item:
        raise InvalidData("At least one of defaults or beneficiario should be set")

    return update_dynamo_item(key, item)
