from decimal import Decimal
from typing import Optional

from incc_shared.models.base import DatetimeNormalizedModel
from incc_shared.models.common import Juros
from incc_shared.models.db.boleto.base import StatusBoleto


class UpdateBoletoModel(DatetimeNormalizedModel):
    valor: Optional[Decimal] = None
    vencimento: Optional[str] = None
    emissao: Optional[str] = None
    pagador: Optional[str] = None
    status: Optional[StatusBoleto] = None
    juros: Optional[Juros] = None
    multa: Optional[Juros] = None
