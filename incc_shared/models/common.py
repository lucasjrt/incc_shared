from decimal import Decimal
from enum import Enum

from pydantic import Field

from incc_shared.models.base import DynamoSerializableModel


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class TipoJuros(str, Enum):
    taxa = "TAXA"
    fixa = "FIXO"
    isenta = "ISENTO"


class Juros(DynamoSerializableModel):
    tipo: TipoJuros
    valor: Decimal
    prazo: int = Field(
        ..., description="Número de dias depois do vencimento para cobrar os juros"
    )
