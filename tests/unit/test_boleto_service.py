from incc_shared.models.request.boleto.create import CreateBoletoModel
from incc_shared.service import table
from incc_shared.service.boleto import create_boleto


def test_create_boleto(testOrgId: str, boleto_data: dict):
    boleto = CreateBoletoModel(**boleto_data)
    nosso_numero = create_boleto(testOrgId, boleto)
    response = table.get_item(
        Key={"tenant": f"ORG#{testOrgId}", "entity": f"BOLETO#{nosso_numero}"}
    )
    assert response, "Boleto was not created"
    print(boleto)
