from decimal import Decimal
from typing import ClassVar, Optional

from pydantic import BaseModel, Field

from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.common import TipoDocumento, TipoJuros


class Beneficiario(BaseModel):
    tipoDocumento: TipoDocumento
    documento: str = Field(..., min_length=11, max_length=14)
    agencia: str = Field(..., min_length=4, max_length=4)
    agenciaDv: str = Field(..., min_length=1, max_length=1)
    convenio: str = Field(..., min_length=6, max_length=7)
    nome: str


class Juros(BaseModel):
    tipo: TipoJuros
    valor: Decimal


class Defaults(BaseModel):
    multa: Juros
    juros: Juros
    comQrcode: bool = False


class OrganizationModel(DynamoBaseModel):
    nossoNumero: int = Field(
        0, description="Gerencia o contador do nosso número para os boletos"
    )
    beneficiario: Optional[Beneficiario] = Field(
        None, description="Dados do beneficiário"
    )
    defaults: Optional[Defaults] = Field(
        None, description="Configurações padrões para a organização"
    )

    ENTITY_TEMPLATE: ClassVar[Optional[str]] = "ORG#{orgId}"
