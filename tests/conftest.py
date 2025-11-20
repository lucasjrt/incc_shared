import os
from datetime import date, timedelta

import boto3
import pytest
from moto import mock_aws
from mypy_boto3_dynamodb.service_resource import Table
from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.create import CreateCustomerModel
from incc_shared.models.request.schedule.create import CreateScheduleModel
from incc_shared.service import get_dynamo_key
from incc_shared.service.customer import create_customer, delete_customer, get_customer
from incc_shared.service.org import create_organization
from incc_shared.service.schedule import create_schedule, delete_schedule, get_schedule

DYNAMODB_TABLE = os.environ["DYNAMODB_TABLE"]
REGION = "sa-east-1"
TEST_TENANT = ULID()


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
def test_org_id(table):
    org_id = TEST_TENANT
    create_organization(org_id)
    yield org_id
    key = get_dynamo_key(org_id, EntityType.organization, org_id)
    table.delete_item(Key=key)


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
def boleto_data(test_customer: CustomerModel):
    today = date.today()
    vencimento = today + timedelta(days=30)
    return {
        "valor": 10,
        "vencimento": vencimento,
        "emissao": today,
        "pagador": test_customer.customerId,
    }


@pytest.fixture
def schedule_data(test_customer: CustomerModel):
    today = date.today()
    vencimento = today + timedelta(days=30)
    dataInicio = today + timedelta(days=7)
    return {
        "valorBase": 10,
        "pagador": test_customer.customerId,
        "vencimento": vencimento,
        "parcelas": 36,
        "dataInicio": dataInicio,
    }


@pytest.fixture
def schedule_balao_data(schedule_data: dict):
    balao_data = schedule_data.copy()
    balao_data["intervaloParcelas"] = 6
    balao_data["parcelas"] = 3
    return balao_data


@pytest.fixture
def test_customer(test_org_id: ULID, customer_data):
    customer_id = create_customer(test_org_id, CreateCustomerModel(**customer_data))
    customer = get_customer(test_org_id, customer_id)
    assert customer
    return customer


@pytest.fixture
def test_customer_2(test_org_id: ULID, customer_data):
    customer_id = create_customer(test_org_id, CreateCustomerModel(**customer_data))
    customer = get_customer(test_org_id, customer_id)
    assert customer
    yield customer
    delete_customer(test_org_id, customer.customerId)


@pytest.fixture
def test_schedule(test_org_id: ULID, schedule_data):
    schedule_id = create_schedule(test_org_id, CreateScheduleModel(**schedule_data))
    schedule = get_schedule(test_org_id, schedule_id)
    assert schedule
    return schedule


@pytest.fixture
def test_schedule_balao(test_org_id: ULID, schedule_balao_data: dict):
    schedule_id = create_schedule(
        test_org_id, CreateScheduleModel(**schedule_balao_data)
    )
    schedule = get_schedule(test_org_id, schedule_id)
    assert schedule
    yield schedule
    delete_schedule(test_org_id, schedule.id)
