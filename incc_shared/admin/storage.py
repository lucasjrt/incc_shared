from typing import Any, Optional, Type

from boto3.dynamodb.conditions import Attr, ConditionBase, Key
from botocore.exceptions import ClientError
from ulid import ULID

from incc_shared.auth.context import get_context_entity
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import Conflict, InvalidState
from incc_shared.models.helper import utc_now_iso
from incc_shared.service.storage.base import M, table, to_model


def admin_get_dynamo_key(org_id: ULID, entityType: EntityType, entityId: ULID | str):
    if isinstance(entityId, ULID):
        entityId = str(entityId)

    return {
        "tenant": f"ORG#{str(org_id)}",
        "entity": f"{entityType.value}#{entityId}",
    }


def admin_create_dynamo_item(item: dict):
    org_id = item.get("orgId")
    if not org_id:
        raise ValueError("Item must have an org_id")

    tenant = f"ORG#{org_id}"
    item["tenant"] = tenant

    entity = item.get("entity")
    if not entity:
        raise ValueError("Item must have an entity")

    item["createdAt"] = utc_now_iso()

    context_user = get_context_entity()
    if not context_user:
        raise InvalidState("No user is set to context during item create")
    item["createdBy"] = context_user.entity

    try:
        table.put_item(
            Item=item,
            ConditionExpression=Attr(tenant).not_exists() & Attr(entity).not_exists(),
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise Conflict("Item already exists")
        else:
            error_message = e.response.get("Error", {}).get("Message")
            print(f"An unexpected error occurred: {error_code} - {error_message}")
            raise


def admin_list_dynamo_entity(org_id: ULID, entity_type: EntityType, model: Type[M]):
    org_key = f"ORG#{org_id}"
    entity_key = f"{entity_type.value}#"
    condition = Key("tenant").eq(org_key) & Key("entity").begins_with(entity_key)

    return list_dynamo_items(condition, model)


def list_dynamo_items(
    condition: ConditionBase, model: Type[M], index_name: Optional[str] = None
):
    kwargs: dict[str, Any] = {
        "KeyConditionExpression": condition,
    }
    if index_name:
        kwargs["IndexName"] = index_name

    response = table.query(**kwargs)

    if response.get("LastEvaluatedKey"):
        # TODO: SNS here, as it's not yet supported
        print("Pagination is expected, user data is now incomplete")

    return [to_model(c, model) for c in response["Items"]]
