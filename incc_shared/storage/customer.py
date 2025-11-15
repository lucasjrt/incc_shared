import ulid
from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError

from incc_shared.exceptions.errors import Conflict, InvalidState, NotFound
from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.models.request.customer.update import UpdateCustomerModel
from incc_shared.storage import patch_dict, table, to_model, update_dynamo_item
from incc_shared.storage.org import get_org


def get_customer(customerId: str):
    customer_key = f"CUSTOMER#{customerId}"

    response = table.query(
        KeyConditionExpression=Key("entity").eq(customer_key),
    )

    if response["Count"] > 1:
        print(
            f"Customer {customer_key} is duplicate in database. It should never happen"
        )
        print(f"Found {response['Count']} occurences in the database")
        raise InvalidState(f"Duplicate user in database: {customer_key}")
    elif response["Count"] == 0:
        print(
            f"Customer {customer_key} not found in database. Complete registration required"
        )

    customer = response["Items"][0]
    return to_model(customer, CustomerModel)


def create_customer(orgId: str, customer: CreateCustomerModel):
    customerId = str(ulid.new())
    model = customer.model_dump()
    model["orgId"] = orgId
    model["customerId"] = customerId

    item = CustomerModel.model_validate(customer.model_dump())
    assert item.entity is not None, "Entity id was expected"

    try:
        table.put_item(
            Item=item.to_item(), ConditionExpression=Attr(item.entity).not_exists()
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise Conflict("Customer already exists")
        else:
            error_message = e.response.get("Error", {}).get("Message")
            print(f"An unexpected error occurred: {error_code} - {error_message}")
            raise


def update_customer(orgId: str, customerId: str, to_update: UpdateCustomerModel):
    customer = get_customer(customerId)
    if not customer:
        return NotFound("Customer not found")

    customer = customer.to_item()
    patch_dict(customer, to_update.model_dump())

    key = {
        "tenant": f"ORG#{orgId}",
        "entity": f"CUSTOMER#{customerId}",
    }
    return update_dynamo_item(key, customer)


def delete_customer(orgId: str, customerId: str):
    key = {
        "tenant": f"ORG#{orgId}",
        "entity": f"CUSTOMER#{customerId}",
    }
    return table.delete_item(Key=key)
