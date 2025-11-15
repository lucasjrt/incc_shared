from typing import Optional

from pydantic import BaseModel

from incc_shared.models.common import TipoDocumento
from incc_shared.models.db.customer import Endereco


class CreateCustomerModel(BaseModel):
    tipoDocumento: TipoDocumento
    documento: str
    nome: str
    endereco: Endereco
    email: Optional[str] = None
    telefone: Optional[str] = None
