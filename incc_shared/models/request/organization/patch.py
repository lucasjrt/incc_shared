from typing import Optional

from pydantic import BaseModel, Field

from incc_shared.models.organization import Defaults


class PatchBeneficiarioModel(BaseModel):
    agencia: str = Field(..., min_length=4, max_length=4)
    agenciaDv: str = Field(..., min_length=1, max_length=1)
    convenio: str = Field(..., min_length=6, max_length=7)


class PatchOrgModel(BaseModel):
    beneficiario: Optional[PatchBeneficiarioModel] = None
    defaults: Optional[Defaults] = None
