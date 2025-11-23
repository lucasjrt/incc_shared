from typing import Optional

from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.db.organization.base import Beneficiario, Defaults


class SetupOrgModel(DynamoSerializableModel):
    beneficiario: Beneficiario
    defaults: Optional[Defaults] = None
