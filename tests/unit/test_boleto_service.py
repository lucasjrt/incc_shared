from datetime import timedelta
from decimal import Decimal

from ulid import ULID

from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.models.request.boleto.update import UpdateBoletoModel
from incc_shared.service import table, to_model
from incc_shared.service.boleto import create_boleto, get_boleto, update_boleto
from incc_shared.service.org import get_org


def test_create_boleto(test_org_id: ULID, boleto_data: dict):
    org = get_org(test_org_id)
    assert org

    nosso_numero = org.nossoNumero

    boleto = CreateBoletoModel(**boleto_data)
    nosso_numero = create_boleto(test_org_id, boleto)
    response = table.get_item(
        Key={"tenant": f"ORG#{test_org_id}", "entity": f"BOLETO#{nosso_numero}"}
    ).get("Item")
    assert response
    new_boleto = to_model(response, BoletoModel)
    assert new_boleto.nossoNumero == nosso_numero
    assert new_boleto.valor == boleto_data["valor"]
    assert new_boleto.vencimento == boleto_data["vencimento"]
    assert new_boleto.emissao == boleto_data["emissao"]
    assert new_boleto.pagador == boleto_data["pagador"]

    org = get_org(test_org_id)
    assert org
    assert org.nossoNumero == nosso_numero + 1

    retrieved_boleto = get_boleto(test_org_id, nosso_numero)
    assert retrieved_boleto == new_boleto

    update_data = {
        "valor": Decimal(boleto.valor + 5),
        "vencimento": boleto_data["vencimento"] + timedelta(days=5),
    }
    update_model = UpdateBoletoModel(**update_data)
    update_boleto(test_org_id, nosso_numero, update_model)

    updated_boleto = get_boleto(test_org_id, nosso_numero)
    assert updated_boleto
    assert updated_boleto != retrieved_boleto
    assert updated_boleto.valor == update_data["valor"]
    assert updated_boleto.vencimento == update_data["vencimento"]
