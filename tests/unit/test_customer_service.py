from incc_shared.models.db.customer import CustomerModel
from incc_shared.models.request.customer.update import UpdateCustomerModel
from incc_shared.service.customer import (
    delete_customer,
    get_customer,
    list_customers,
    update_customer,
)
from incc_shared.service.storage.base import to_model


def test_customer_lifecycle(
    test_customer: CustomerModel,
    customer_data: dict,
    test_customer_2: CustomerModel,
):
    assert test_customer.tipoDocumento == customer_data["tipoDocumento"]
    assert test_customer.documento == customer_data["documento"]
    assert test_customer.nome == customer_data["nome"]
    assert test_customer.endereco.logradouro == customer_data["endereco"]["logradouro"]
    assert test_customer.endereco.bairro == customer_data["endereco"]["bairro"]
    assert test_customer.endereco.cidade == customer_data["endereco"]["cidade"]
    assert test_customer.endereco.uf == customer_data["endereco"]["uf"]
    assert test_customer.endereco.cep == customer_data["endereco"]["cep"]

    customer = get_customer(test_customer.customerId)
    assert customer is not None

    customers = list_customers()
    assert len(customers) == 2
    ids = [test_customer.customerId, test_customer_2.customerId]
    for c in customers:
        assert c.customerId in ids

    update_fields = {
        "email": "john.doe@example.com",
        "telefone": "9999999999",
    }
    update_model = to_model(update_fields, UpdateCustomerModel)

    update_customer(test_customer.customerId, update_model)
    updated_customer = get_customer(test_customer.customerId)
    assert updated_customer
    assert updated_customer.email == update_model.email
    assert updated_customer.telefone == update_model.telefone

    delete_customer(test_customer.customerId)
    assert get_customer(test_customer.customerId) is None
