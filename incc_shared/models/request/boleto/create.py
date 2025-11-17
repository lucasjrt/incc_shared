from typing import Optional

from pydantic import Field

from incc_shared.models.common import Juros
from incc_shared.models.db.boleto.base import BoletoBase, StatusBoleto


class CreateBoletoModel(BoletoBase):
    nossoNumero: int = Field(0, exclude=True)
    status: StatusBoleto = Field(StatusBoleto.desconhecido, exclude=True)
    juros: Optional[Juros] = None
    multa: Optional[Juros] = None
