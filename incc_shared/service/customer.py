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
    list_dynamo_items,
    update_dynamo_item,
)


def get_customer(orgId: str, customerId: str):
    key = get_dynamo_key(orgId, EntityType.customer, customerId)
    return get_dynamo_item(key, CustomerModel)


def list_customers(orgId: str):
    return list_dynamo_items(orgId, EntityType.customer, CustomerModel)


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
