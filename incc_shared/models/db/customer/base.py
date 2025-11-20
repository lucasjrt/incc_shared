from typing import Optional

from pydantic import Field
from ulid import ULID

from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.common import TipoDocumento


class Endereco(DynamoSerializableModel):
    logradouro: str
    bairro: str
    cidade: str
    uf: str = Field(..., min_length=2, max_length=2)
    cep: str = Field(..., min_length=8, max_length=8)


class CustomerBase(DynamoSerializableModel):
    customerId: ULID
    nome: str
    tipoDocumento: TipoDocumento
    documento: str
    endereco: Endereco
    email: Optional[str] = None
    telefone: Optional[str] = None
