import os
from datetime import datetime, timedelta
from typing import Any

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb.service_resource import Table

from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.organization import OrganizationModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.service import to_model
from incc_shared.service.customer import create_customer, delete_customer

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
REGION = "sa-east-1"
TEST_TENANT = "01KA13K7YAHB6R1ECCS8FQDDZJ"


@pytest.fixture(scope="session")
def table():
    """Start moto once per test session and create the real table once."""
    with mock_aws():
        # create resource and table
        dynamo = boto3.resource("dynamodb", region_name=REGION)
        new_table = dynamo.create_table(
            TableName=DYNAMODB_TABLE,
            KeySchema=[
                {"AttributeName": "tenant", "KeyType": "HASH"},
                {"AttributeName": "entity", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "tenant", "AttributeType": "S"},
                {"AttributeName": "entity", "AttributeType": "S"},
                {"AttributeName": "gsi_user_pk", "AttributeType": "S"},
                {"AttributeName": "gsi_email_pk", "AttributeType": "S"},
                {"AttributeName": "gsi_org_sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "user_index",
                    "KeySchema": [
                        {"AttributeName": "gsi_user_pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi_org_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": ["features", "roles"],
                    },
                },
                {
                    "IndexName": "email_index",
                    "KeySchema": [
                        {"AttributeName": "gsi_email_pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi_org_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {
                        "ProjectionType": "INCLUDE",
                        "NonKeyAttributes": ["features", "roles"],
                    },
                },
            ],
        )
        new_table.wait_until_exists()
        new_table = dynamo.Table(DYNAMODB_TABLE)
        yield new_table


@pytest.fixture(autouse=True)
def clean_table_between_tests(table: Table):
    """Ensure every test runs on a clean table (delete all items before test)."""
    # delete everything before test
    resp = table.scan(ProjectionExpression="tenant, entity")
    items = resp.get("Items", [])
    with table.batch_writer() as bw:
        for it in items:
            bw.delete_item(Key={"tenant": it["tenant"], "entity": it["entity"]})
    yield
    # also delete after test (in case test added items)
    resp = table.scan(ProjectionExpression="tenant, entity")
    items = resp.get("Items", [])
    with table.batch_writer() as bw:
        for it in items:
            bw.delete_item(Key={"tenant": it["tenant"], "entity": it["entity"]})


@pytest.fixture
def testOrgId(table):
    orgId = TEST_TENANT
    org_attr: dict[str, Any] = {"orgId": orgId}
    organization = OrganizationModel(**org_attr)
    table.put_item(Item=organization.to_item())
    yield orgId
    table.delete_item(Key={"tenant": f"ORG#{orgId}", "entity": f"ORG#{orgId}"})


@pytest.fixture
def customer_data():
    return {
        "tipoDocumento": "CPF",
        "documento": "01234567890",
        "nome": "Fulano de Tal da Silva",
        "endereco": {
            "logradouro": "Rua dos Bobos, 0",
            "bairro": "Madagascar",
            "cidade": "Pensilvânia",
            "uf": "MG",
            "cep": "38400000",
        },
    }


@pytest.fixture
def customer_data2():
    return {
        "tipoDocumento": "CPF",
        "documento": "98765432100",
        "nome": "Beltrano Pereira dos Anzóis",
        "endereco": {
            "logradouro": "Avenida das Acácias, 1234",
            "bairro": "Jardim do Sol",
            "cidade": "Serra Azul",
            "uf": "SP",
            "cep": "13579000",
        },
    }


@pytest.fixture
def boleto_data(testCustomer: CustomerModel):
    today = datetime.today()
    vencimento = today + timedelta(days=30)
    return {
        "valor": 10,
        "vencimento": vencimento.date(),
        "emissao": today.date(),
        "pagador": testCustomer.customerId,
    }


@pytest.fixture
def testCustomer(table: Table, testOrgId: str, customer_data):
    customerId = create_customer(testOrgId, CreateCustomerModel(**customer_data))
    result = table.get_item(
        Key={"tenant": f"ORG#{testOrgId}", "entity": f"CUSTOMER#{customerId}"}
    )
    item = result.get("Item")
    assert item
    retrieved = to_model(item, CustomerModel)
    return retrieved


@pytest.fixture
def testCustomer2(table: Table, testOrgId: str, customer_data):
    customerId = create_customer(testOrgId, CreateCustomerModel(**customer_data))
    result = table.get_item(
        Key={"tenant": f"ORG#{testOrgId}", "entity": f"CUSTOMER#{customerId}"}
    )
    item = result.get("Item")
    assert item
    retrieved = to_model(item, CustomerModel)
    yield retrieved
    delete_customer(testOrgId, retrieved.customerId)
