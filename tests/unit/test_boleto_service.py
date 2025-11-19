from datetime import timedelta
from decimal import Decimal

from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.boleto.update import UpdateBoletoModel
from incc_shared.service import table, to_model
from incc_shared.service.boleto import create_boleto, get_boleto, update_boleto
from incc_shared.service.org import get_org
from incc_shared.service.utils import format_date


def test_create_boleto(testOrgId: str, boleto_data: dict):
    org = get_org(testOrgId)
    assert org

    nosso_numero = org.nossoNumero

    boleto = CreateBoletoModel(**boleto_data)
    nosso_numero = create_boleto(testOrgId, boleto)
    response = table.get_item(
        Key={"tenant": f"ORG#{testOrgId}", "entity": f"BOLETO#{nosso_numero}"}
    ).get("Item")
    assert response
    new_boleto = to_model(response, BoletoModel)
    assert new_boleto.nossoNumero == nosso_numero
    assert new_boleto.valor == boleto_data["valor"]
    assert new_boleto.vencimento == boleto_data["vencimento"].strftime("%Y-%m-%d")
    assert new_boleto.emissao == boleto_data["emissao"].strftime("%Y-%m-%d")
    assert new_boleto.pagador == boleto_data["pagador"]

    org = get_org(testOrgId)
    assert org
    assert org.nossoNumero == nosso_numero + 1

    retrieved_boleto = get_boleto(testOrgId, nosso_numero)
    assert retrieved_boleto == new_boleto

    update_data = {
        "valor": Decimal(boleto.valor + 5),
        "vencimento": boleto_data["vencimento"] + timedelta(days=5),
    }
    update_model = UpdateBoletoModel(**update_data)
    update_boleto(testOrgId, nosso_numero, update_model)

    updated_boleto = get_boleto(testOrgId, nosso_numero)
    assert updated_boleto
    assert updated_boleto != retrieved_boleto
    assert updated_boleto.valor == update_data["valor"]
    assert updated_boleto.vencimento == format_date(update_data["vencimento"])
