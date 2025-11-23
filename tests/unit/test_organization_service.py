import pytest

from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.common import TipoDocumento
from incc_shared.models.request.organization.org_setup import SetupOrgModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service.organization import (
    get_org,
    setup_organization,
    update_organization,
)
from incc_shared.service.storage.base import to_model


def test_org_lifecycle():
    org = get_org()
    assert org
    assert org.beneficiario is None
    assert org.defaults is None

    setup_fields = {
        "beneficiario": {
            "tipoDocumento": TipoDocumento.CNPJ,
            "documento": "00111222000133",
            "nome": "Lorem Ipsum Inc.",
            "agencia": "1234",
            "agenciaDv": "1",
            "convenio": "1234567",
        }
    }

    update_fields = {
        "beneficiario": {
            "agencia": "4321",
            "agenciaDv": "0",
            "convenio": "7654321",
        }
    }
    update_model = to_model(update_fields, UpdateOrganizationModel)

    with pytest.raises(InvalidState):
        update_organization(update_model)

    setup_model = to_model(setup_fields, SetupOrgModel)
    setup_organization(setup_model)

    update_organization(update_model)
    updated_org = get_org()
    assert updated_org
    assert updated_org.beneficiario
    assert updated_org.beneficiario.agencia == update_fields["beneficiario"]["agencia"]
    assert (
        updated_org.beneficiario.agenciaDv == update_fields["beneficiario"]["agenciaDv"]
    )
    assert (
        updated_org.beneficiario.convenio == update_fields["beneficiario"]["convenio"]
    )
