from datetime import date
from decimal import Decimal
from typing import Optional

from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.common import Juros
from incc_shared.models.db.boleto.base import StatusBoleto


class UpdateBoletoModel(DynamoSerializableModel):
    valor: Optional[Decimal] = None
    vencimento: Optional[date] = None
    emissao: Optional[date] = None
    pagador: Optional[str] = None
    status: Optional[StatusBoleto] = None
    juros: Optional[Juros] = None
    multa: Optional[Juros] = None
