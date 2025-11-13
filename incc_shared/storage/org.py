from boto3.dynamodb.conditions import Key

from incc_shared.exceptions import BadRequest, ServerError
from incc_shared.models.organization import OrganizationModel
from incc_shared.storage import table, to_model, update_dynamo_item


def get_org(orgId: str):
    org_key = f"ORG#{orgId}"
    query = table.query(
        KeyConditionExpression=Key("tenant").eq(org_key) & Key("entity").eq(org_key)
    )

    if len(query["Items"]) == 0:
        return None
    elif len(query["Items"]) > 1:
        raise ServerError("Invalid state: More than one org was found with same ID")

    return to_model(query["Items"][0], OrganizationModel)


def update_org(orgId: str, org: OrganizationModel):
    if orgId != org.orgId:
        raise BadRequest("Cannot change org id")

    tenant_key = f"ORG#{orgId}"
    key = {
        "tenant": tenant_key,
        "entity": tenant_key,
    }
    return update_dynamo_item(key, org.to_item())
