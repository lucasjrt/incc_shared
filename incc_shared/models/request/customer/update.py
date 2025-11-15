from typing import Optional

from pydantic import BaseModel

from incc_shared.models import TipoDocumento
from incc_shared.models.db.customer import Endereco


class UpdateCustomerModel(BaseModel):
    tipoDocumento: TipoDocumento
    documento: str
    nome: Optional[str] = None
    endereco: Optional[Endereco]
    email: Optional[str] = None
    telefone: Optional[str] = None
