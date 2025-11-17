from typing import Optional

from pydantic import BaseModel

from incc_shared.models.common import TipoDocumento
from incc_shared.models.db.customer.base import Endereco


class UpdateCustomerModel(BaseModel):
    tipoDocumento: Optional[TipoDocumento] = None
    documento: Optional[str] = None
    nome: Optional[str] = None
    endereco: Optional[Endereco] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
