from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel

from incc_shared.models.base import DatetimeNormalizedModel
from incc_shared.models.common import Juros


class StatusBoleto(str, Enum):
    atualizado = "ATUALIZADO"
    cancelado = "CANCELADO"
    desconhecido = "DESCONHECIDO"
    falhou = "FALHOU"
    emitido = "EMITIDO"
    enviado = "ENVIADO"
    pago = "PAGO"


class BoletoBase(DatetimeNormalizedModel, BaseModel):
    nossoNumero: int
    valor: Decimal
    vencimento: str
    emissao: str
    pagador: str
    status: StatusBoleto
    # The fields below are only optional so that the request can inherit it, but
    # they're actually required
    juros: Optional[Juros]
    multa: Optional[Juros]
