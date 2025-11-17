from incc_shared.models.db.boleto.boleto import BoletoModel
from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.service import table, to_model
from incc_shared.service.boleto import create_boleto
from incc_shared.service.org import get_org


def test_create_boleto(testOrgId: str, boleto_data: dict):
    org = get_org(testOrgId)
    assert org

    # Reference only
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
