from datetime import date
from enum import Enum
from typing import List, Optional

from ulid import ULID

from incc_shared.models import ConstrainedMoney
from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.common import Juros


class StatusBoleto(str, Enum):
    atualizado = "ATUALIZADO"
    cancelado = "CANCELADO"
    desconhecido = "DESCONHECIDO"
    falhou = "FALHOU"
    emitido = "EMITIDO"
    enviado = "ENVIADO"
    pago = "PAGO"


class BoletoBase(DynamoSerializableModel):
    nossoNumero: int
    valor: ConstrainedMoney
    vencimento: date
    emissao: date
    pagador: ULID
    status: List[StatusBoleto]
    # The fields below are only optional so that the request can inherit it, but
    # they're actually required
    juros: Optional[Juros]
    multa: Optional[Juros]
