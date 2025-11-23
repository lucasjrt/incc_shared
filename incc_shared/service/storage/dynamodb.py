from typing import Any, Optional, Type

from boto3.dynamodb.conditions import Attr, ConditionBase, Key
from botocore.exceptions import ClientError
from ulid import ULID

from incc_shared.auth.context import get_context_entity
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import Conflict, InvalidState
from incc_shared.models.helper import utc_now_iso
from incc_shared.service.storage.base import M, table, to_model


def get_dynamo_key(entityType: EntityType, entityId: ULID | str):
    user = get_context_entity()
    if isinstance(entityId, ULID):
        entityId = str(entityId)

    return {
        "tenant": f"ORG#{str(user.orgId)}",
        "entity": f"{entityType.value}#{entityId}",
    }


def get_dynamo_item(dynamo_key: dict, model: Type[M]):
    item = table.get_item(Key=dynamo_key).get("Item")
    if item:
        return to_model(item, model)

    return None


def get_dyanmo_index_item(index_name: str, condition: ConditionBase, model: Type[M]):
    response = table.query(IndexName=index_name, KeyConditionExpression=condition)

    items = response.get("Items", [])
    if len(items) > 1:
        raise InvalidState(
            f"{len(items)} items was found in index {index_name} for the given key"
        )

    if items:
        return to_model(items[0], model)

    return None


def _flatten_updates(
    prefix: tuple[str, ...],
    obj: Any,
    out: dict[tuple[str, ...], Any],
    exclude_none: bool = True,
):
    """
    Takes a dict and return a tuple to a value.
    Example
        {'a': {'b': 'c'}} -> {('a', 'b'): 'c'}
    """
    if isinstance(obj, dict):
        for k, v in obj.items():
            _flatten_updates(prefix + (k,), v, out)
    else:
        if exclude_none and obj is None:
            return
        out[prefix] = obj


def update_dynamo_item(key: dict, update: dict):
    update.pop("tenant", None)
    update.pop("entity", None)
    update["updatedAt"] = utc_now_iso()

    context_user = get_context_entity()
    if not context_user:
        raise InvalidState("No user is set to context during item update")
    update["updatedBy"] = context_user.entity

    flat: dict[tuple[str, ...], Any] = {}
    for k, v in update.items():
        _flatten_updates((k,), v, flat)

    set_clauses = []
    expr_names = {}
    expr_vals = {}
    for i, (path_tuple, value) in enumerate(flat.items()):
        name_placeholders = []
        for j, seg in enumerate(path_tuple):
            ph = f"#n{i}_{j}"
            name_placeholders.append(ph)
            expr_names[ph] = seg
        path_expr = ".".join(name_placeholders)
        val_key = f":v{i}"
        set_clauses.append(f"{path_expr} = {val_key}")
        expr_vals[val_key] = value

    if not set_clauses:
        return None

    update_expr = "SET " + ", ".join(set_clauses)
    resp = table.update_item(
        Key=key,
        UpdateExpression=update_expr,
        ExpressionAttributeNames=expr_names,
        ExpressionAttributeValues=expr_vals,
        ReturnValues="ALL_NEW",
    )
    return resp.get("Attributes")


def set_dynamo_item(to_set: dict):
    """Sets the fields to an existing item"""
    to_set["updatedAt"] = utc_now_iso()

    context_user = get_context_entity()
    if not context_user:
        raise InvalidState("No user is set to context during item update")
    to_set["updatedBy"] = context_user.entity
    org_id = str(context_user.orgId)
    to_set["orgId"] = org_id
    to_set["tenant"] = f"ORG#{org_id}"

    try:
        resp = table.put_item(
            Item=to_set,
            ConditionExpression=Attr("tenant").exists() & Attr("entity").exists(),
        )
        return resp.get("Attributes")
    except ClientError as e:
        if e.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
            raise InvalidState("Item does not exist for the given tenant/entity") from e
        raise


def create_dynamo_item(item: dict):
    context_user = get_context_entity()
    org_id = str(context_user.orgId)
    if not org_id:
        raise ValueError("Item must have an org_id")

    tenant = f"ORG#{org_id}"
    item["tenant"] = tenant
    item["orgId"] = org_id

    entity = item.get("entity")
    if not entity:
        raise ValueError("Item must have an entity")

    item["createdAt"] = utc_now_iso()
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


def patch_dict(whole: dict, to_patch: dict, ignore_nulls: bool = True):
    whole.update(
        {
            k: v
            for k, v in to_patch.items()
            if k in whole and (not ignore_nulls or v is not None)
        }
    )


def fill_dict(filling: dict, filler: dict):
    for key in filling:
        if key in filler:
            filling[key] = filler[key]


def delete_dynamo_item(key: dict):
    table.delete_item(Key=key)


def list_dynamo_entity(entity_type: EntityType, model: Type[M]):
    user = get_context_entity()
    org_id = str(user.orgId)
    if not org_id:
        raise ValueError("Item must have an org_id")

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
