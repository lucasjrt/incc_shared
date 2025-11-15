from typing import Optional

from pydantic import BaseModel

from incc_shared.models.db.customer import Endereco


class UpdateCustomerModel(BaseModel):
    nome: Optional[str] = None
    endereco: Optional[Endereco]
    email: Optional[str] = None
    telefone: Optional[str] = None
