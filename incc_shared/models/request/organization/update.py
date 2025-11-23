from typing import Optional

from pydantic import Field

from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.db.organization import Defaults


class UpdateBeneficiarioModel(DynamoSerializableModel):
    agencia: str = Field(..., min_length=4, max_length=4)
    agenciaDv: str = Field(..., min_length=1, max_length=1)
    convenio: str = Field(..., min_length=6, max_length=7)


class UpdateOrganizationModel(DynamoSerializableModel):
    beneficiario: Optional[UpdateBeneficiarioModel] = None
    defaults: Optional[Defaults] = None
    nossoNumero: Optional[int] = None
