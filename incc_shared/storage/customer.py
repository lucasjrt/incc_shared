from boto3.dynamodb.conditions import Attr, Key
from botocore.exceptions import ClientError
from ulid import ULID

from incc_shared.exceptions.errors import Conflict, InvalidState, NotFound
from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.models.request.customer.update import UpdateCustomerModel
from incc_shared.storage import (
    fill_dict,
    patch_dict,
    table,
    to_model,
    update_dynamo_item,
)


def get_customer(orgId: str, customerId: str):
    org_key = f"ORG#{orgId}"
    customer_key = f"CUSTOMER#{customerId}"

    response = table.get_item(Key={"tenant": org_key, "entity": customer_key})

    customer = response.get("Item")
    if not customer:
        return None

    return to_model(customer, CustomerModel)


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
    model["orgId"] = orgId
    model["customerId"] = customerId

    item = CustomerModel.model_validate(model)
    assert item.entity is not None, "Entity id was expected"

    try:
        table.put_item(
            Item=item.to_item(), ConditionExpression=Attr(item.entity).not_exists()
        )
        return customerId
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise Conflict("Customer already exists")
        else:
            error_message = e.response.get("Error", {}).get("Message")
            print(f"An unexpected error occurred: {error_code} - {error_message}")
            raise


def update_customer(orgId: str, customerId: str, to_update: UpdateCustomerModel):
    customer = get_customer(orgId, customerId)
    if not customer:
        return NotFound("Customer not found")

    customer = customer.to_item()
    model_fields = UpdateCustomerModel().model_dump()
    fill_dict(model_fields, customer)
    print("Model field:", model_fields)
    patch_dict(model_fields, to_update.model_dump())

    key = {
        "tenant": f"ORG#{orgId}",
        "entity": f"CUSTOMER#{customerId}",
    }

    print("Fields to update model:", model_fields)
    return update_dynamo_item(key, model_fields)


def delete_customer(orgId: str, customerId: str):
    key = {
        "tenant": f"ORG#{orgId}",
        "entity": f"CUSTOMER#{customerId}",
    }
    return table.delete_item(Key=key)
