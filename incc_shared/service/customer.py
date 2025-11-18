from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import Conflict, InvalidState
from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.models.request.customer.update import UpdateCustomerModel
from incc_shared.service import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    table,
    to_model,
    update_dynamo_item,
)


def get_customer(orgId: str, customerId: str):
    key = get_dynamo_key(orgId, EntityType.customer, customerId)
    return get_dynamo_item(key, CustomerModel)


def list_customers(orgId: str):
    org_key = f"ORG#{orgId}"
    customer_key = "CUSTOMER#"
    response = table.query(
        KeyConditionExpression=Key("tenant").eq(org_key)
        & Key("entity").begins_with(customer_key),
    )

    if response.get("LastEvaluatedKey"):
        raise InvalidState("App is not yet prepared to receive more pages")

    return [to_model(c, CustomerModel) for c in response["Items"]]


def create_customer(orgId: str, customer: CreateCustomerModel):
    customerId = str(ULID())
    model = customer.model_dump()
    item = CustomerModel(orgId=orgId, customerId=customerId, **model)

    create_dynamo_item(item.to_item())
    return customerId


def update_customer(orgId: str, customerId: str, to_update: UpdateCustomerModel):
    key = get_dynamo_key(orgId, EntityType.customer, customerId)
    return update_dynamo_item(key, to_update.model_dump())


def delete_customer(orgId: str, customerId: str):
    key = get_dynamo_key(orgId, EntityType.customer, customerId)
    delete_dynamo_item(key)
    return customerId
