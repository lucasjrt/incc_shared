from datetime import timedelta
from decimal import Decimal

from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.boleto.update import UpdateBoletoModel
from incc_shared.service.boleto import create_boleto, get_boleto, update_boleto
from incc_shared.service.organization import get_org


def test_create_boleto(boleto_data: dict):
    org = get_org()
    assert org

    nosso_numero = org.nossoNumero

    model = CreateBoletoModel(**boleto_data)
    nosso_numero = create_boleto(model)
    boleto = get_boleto(nosso_numero)
    assert boleto
    assert boleto.nossoNumero == nosso_numero
    assert boleto.valor == boleto_data["valor"]
    assert boleto.vencimento == boleto_data["vencimento"]
    assert boleto.emissao == boleto_data["emissao"]
    assert boleto.pagador == boleto_data["pagador"]

    org = get_org()
    assert org
    assert org.nossoNumero == nosso_numero + 1

    update_data = {
        "valor": Decimal(model.valor + 5),
        "vencimento": boleto_data["vencimento"] + timedelta(days=5),
    }
    update_model = UpdateBoletoModel(**update_data)
    update_boleto(nosso_numero, update_model)

    updated_boleto = get_boleto(nosso_numero)
    assert updated_boleto
    assert updated_boleto != boleto
    assert updated_boleto.valor == update_data["valor"]
    assert updated_boleto.vencimento == update_data["vencimento"]
