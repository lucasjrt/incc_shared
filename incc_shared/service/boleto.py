from decimal import Decimal

from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.common import Juros, TipoJuros
from incc_shared.models.db.boleto.base import StatusBoleto
from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.organization import OrganizationModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.boleto.update import UpdateBoletoModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_items,
    update_dynamo_item,
)
from incc_shared.service.org import get_org, update_organization


def get_boleto(orgId: str, nossoNumero: int):
    key = get_dynamo_key(orgId, EntityType.boleto, str(nossoNumero))
    return get_dynamo_item(key, BoletoModel)


def update_nosso_numero(org: OrganizationModel):
    nossoNumero = org.nossoNumero + 1
    patch_org = UpdateOrganizationModel(nossoNumero=nossoNumero)
    update_organization(org.orgId, patch_org)


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
    item = BoletoModel(
        orgId=orgId,
        nossoNumero=nosso_numero,
        status=[StatusBoleto.emitido],
        **model,
    )

    # TODO: Criar boleto da caixa aqui e, se der errado, solta uma exceção

    create_dynamo_item(item.to_item())

    update_nosso_numero(org)

    return nosso_numero


def update_boleto(orgId: str, nosso_numero: int, boleto: UpdateBoletoModel):
    key = get_dynamo_key(orgId, EntityType.boleto, str(nosso_numero))
    update_dynamo_item(key, boleto.model_dump())


def delete_boleto(orgId: str, nosso_numero: int):
    key = get_dynamo_key(orgId, EntityType.boleto, str(nosso_numero))
    delete_dynamo_item(key)


def list_boletos(orgId: str):
    return list_dynamo_items(orgId, EntityType.boleto, BoletoModel)
