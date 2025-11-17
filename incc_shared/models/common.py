from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class TipoJuros(str, Enum):
    taxa = "TAXA"
    fixa = "FIXO"
    isenta = "ISENTO"


class Juros(BaseModel):
    tipo: TipoJuros
    valor: Decimal
    prazo: int = Field(
        ..., description="Número de dias depois do vencimento para cobrar os juros"
    )
