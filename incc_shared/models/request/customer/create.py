from typing import Optional

from pydantic import BaseModel

from incc_shared.models import TipoDocumento
from incc_shared.models.db.customer import Endereco


class CreateCustomerModel(BaseModel):
    nome: str
    tipoDocumento: TipoDocumento
    documento: str
    endereco: Endereco
    email: Optional[str] = None
    telefone: Optional[str] = None
