from decimal import Decimal

from boto3.dynamodb.conditions import Attr
from botocore.exceptions import ClientError

from incc_shared.exceptions.errors import Conflict, InvalidState
from incc_shared.models.common import Juros, TipoJuros
from incc_shared.models.db.boleto.base import StatusBoleto
from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.organization import OrganizationModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.service import table, update_dynamo_item
from incc_shared.service.org import get_org


def update_nosso_numero(org: OrganizationModel):
    org.nossoNumero += 1
    key = {
        "tenant": f"ORG#{org.orgId}",
        "entity": f"ORG#{org.orgId}",
    }
    item = org.to_item()
    del item["tenant"]
    del item["entity"]
    update_dynamo_item(key, item)
    return org


def get_default_juros():
    return Juros(tipo=TipoJuros.taxa, valor=Decimal(1), prazo=0)


def get_default_multa():
    return Juros(tipo=TipoJuros.taxa, valor=Decimal(2), prazo=0)


def create_boleto(orgId: str, boleto: CreateBoletoModel):
    org = get_org(orgId)
    if not org:
        raise InvalidState("Org does not exist")

    nosso_numero = org.nossoNumero

    if not boleto.juros:
        if org.defaults:
            boleto.juros = org.defaults.juros
        else:
            boleto.juros = get_default_juros()

    if not boleto.multa:
        if org.defaults:
            boleto.multa = org.defaults.multa
        else:
            boleto.multa = get_default_multa()

    model = boleto.model_dump()
    model["orgId"] = orgId
    model["nossoNumero"] = nosso_numero
    model["status"] = StatusBoleto.emitido

    item = BoletoModel.model_validate(model)
    assert item.tenant is not None, "Tenant id was expected"
    assert item.entity is not None, "Entity id was expected"

    try:
        table.put_item(
            Item=item.to_item(),
            ConditionExpression=Attr(item.tenant).not_exists()
            & Attr(item.entity).not_exists(),
        )
    except ClientError as e:
        error_code = e.response.get("Error", {}).get("Code")
        if error_code == "ConditionalCheckFailedException":
            raise Conflict("Customer already exists")
        else:
            error_message = e.response.get("Error", {}).get("Message")
            print(f"An unexpected error occurred: {error_code} - {error_message}")
            raise

    update_nosso_numero(org)

    return nosso_numero


def update_boleto():
    pass


def delete_boleto():
    pass


def get_boleto():
    pass


def list_boletos():
    pass
