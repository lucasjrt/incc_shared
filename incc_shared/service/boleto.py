from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.common import get_default_juros, get_default_multa
from incc_shared.models.db.boleto.base import StatusBoleto
from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.db.organization import OrganizationModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.boleto.update import UpdateBoletoModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service.organization import get_org, update_organization
from incc_shared.service.storage.dynamodb import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
    update_dynamo_item,
)


def get_boleto(nosso_numero: int):
    key = get_dynamo_key(EntityType.boleto, str(nosso_numero))
    return get_dynamo_item(key, BoletoModel)


def update_nosso_numero(org: OrganizationModel):
    nossoNumero = org.nossoNumero + 1
    patch_org = UpdateOrganizationModel(nossoNumero=nossoNumero)
    update_organization(patch_org)


def create_boleto(boleto: CreateBoletoModel):
    org = get_org()
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

    model = boleto.to_item()
    item = BoletoModel(
        nossoNumero=nosso_numero,
        status=[StatusBoleto.emitido],
        **model,
    )

    # TODO: Criar boleto da caixa aqui e, se der errado, solta uma exceção

    create_dynamo_item(item.to_item())

    update_nosso_numero(org)

    return nosso_numero


def update_boleto(nosso_numero: int, boleto: UpdateBoletoModel):
    key = get_dynamo_key(EntityType.boleto, str(nosso_numero))
    update_dynamo_item(key, boleto.to_item())


def delete_boleto(nosso_numero: int):
    key = get_dynamo_key(EntityType.boleto, str(nosso_numero))
    delete_dynamo_item(key)


def list_boletos():
    return list_dynamo_entity(EntityType.boleto, BoletoModel)
