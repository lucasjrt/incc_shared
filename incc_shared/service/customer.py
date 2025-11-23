from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.models.request.customer.update import UpdateCustomerModel
from incc_shared.service.storage.dynamodb import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
    update_dynamo_item,
)


def get_customer(customerId: ULID):
    key = get_dynamo_key(EntityType.customer, customerId)
    return get_dynamo_item(key, CustomerModel)


def list_customers():
    return list_dynamo_entity(EntityType.customer, CustomerModel)


def create_customer(customer: CreateCustomerModel):
    customerId = ULID()
    model = customer.to_item()
    item = CustomerModel(customerId=customerId, **model)

    create_dynamo_item(item.to_item())
    return customerId


def update_customer(customerId: ULID, to_update: UpdateCustomerModel):
    key = get_dynamo_key(EntityType.customer, customerId)
    return update_dynamo_item(key, to_update.to_item())


def delete_customer(customerId: ULID):
    key = get_dynamo_key(EntityType.customer, customerId)
    delete_dynamo_item(key)
    return customerId
