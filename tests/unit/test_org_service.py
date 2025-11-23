import pytest

from incc_shared.exceptions.errors import InvalidState
from incc_shared.models.common import TipoDocumento
from incc_shared.models.db.organization.base import Beneficiario
from incc_shared.models.request.organization.org_setup import SetupOrgModel
from incc_shared.models.request.organization.update import UpdateOrganizationModel
from incc_shared.service import to_model
from incc_shared.service.org import (
    create_organization,
    get_org,
    setup_organization,
    update_organization,
)


def test_org_lifecycle():
    org_id = create_organization()
    org = get_org(org_id)
    assert org
    assert org.orgId == org_id
    assert org.beneficiario is None
    assert org.defaults is None
    assert org.nossoNumero == 1

    setup_fields = {
        "tipoDocumento": TipoDocumento.CNPJ,
        "documento": "00111222000133",
        "nome": "Lorem Ipsum Inc.",
        "agencia": "1234",
        "agenciaDv": "1",
        "convenio": "1234567",
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
        update_organization(org.orgId, update_model)

    beneficiario = Beneficiario(**setup_fields)
    setup_model = SetupOrgModel(beneficiario=beneficiario)
    setup_organization(org_id, setup_model)

    update_organization(org.orgId, update_model)
    updated_org = get_org(org.orgId)
    assert updated_org
    assert updated_org.beneficiario
    assert updated_org.beneficiario.agencia == update_fields["beneficiario"]["agencia"]
    assert (
        updated_org.beneficiario.agenciaDv == update_fields["beneficiario"]["agenciaDv"]
    )
    assert (
        updated_org.beneficiario.convenio == update_fields["beneficiario"]["convenio"]
    )
