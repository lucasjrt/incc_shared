from datetime import date
from decimal import Decimal
from typing import Optional

from ulid import ULID

from incc_shared.models.base import DynamoSerializableModel


class UpdateScheduleModel(DynamoSerializableModel):
    ativo: Optional[bool] = None
    valorBase: Optional[Decimal] = None
    pagador: Optional[ULID] = None
    vencimento: Optional[date] = None
    parcelas: Optional[int] = None
    dataInicio: Optional[date] = None
