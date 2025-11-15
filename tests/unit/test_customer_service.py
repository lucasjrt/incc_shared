from incc_shared.models.db.customer import CustomerModel
from incc_shared.storage.customer import delete_customer, get_customer, list_customers


def test_customer_lifecycle(
    testOrgId: str,
    testCustomer: CustomerModel,
    customer_data: dict,
    testCustomer2: CustomerModel,
):
    assert testCustomer.tipoDocumento == customer_data["tipoDocumento"]
    assert testCustomer.documento == customer_data["documento"]
    assert testCustomer.nome == customer_data["nome"]
    assert testCustomer.endereco.logradouro == customer_data["endereco"]["logradouro"]
    assert testCustomer.endereco.bairro == customer_data["endereco"]["bairro"]
    assert testCustomer.endereco.cidade == customer_data["endereco"]["cidade"]
    assert testCustomer.endereco.uf == customer_data["endereco"]["uf"]
    assert testCustomer.endereco.cep == customer_data["endereco"]["cep"]

    customer = get_customer(testOrgId, testCustomer.customerId)
    assert customer is not None

    customers = list_customers(testOrgId)
    assert len(customers) == 2
    ids = [testCustomer.customerId, testCustomer2.customerId]
    for c in customers:
        assert c.customerId in ids

    delete_customer(testOrgId, testCustomer.customerId)
    assert get_customer(testOrgId, testCustomer.customerId) is None
