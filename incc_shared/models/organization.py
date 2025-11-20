from typing import ClassVar, Optional

from pydantic import Field

from incc_shared.models.base import DynamoBaseModel, DynamoSerializableModel
from incc_shared.models.common import Juros, TipoDocumento


class Beneficiario(DynamoSerializableModel):
    tipoDocumento: TipoDocumento
    documento: str = Field(..., min_length=11, max_length=14)
    agencia: str = Field(..., min_length=4, max_length=4)
    agenciaDv: str = Field(..., min_length=1, max_length=1)
    convenio: str = Field(..., min_length=6, max_length=7)
    nome: str


class Defaults(DynamoSerializableModel):
    multa: Juros
    juros: Juros
    comQrcode: bool = False


class OrganizationModel(DynamoBaseModel):
    nossoNumero: int = Field(
        1, description="Gerencia o contador do nosso número para os boletos"
    )
    beneficiario: Optional[Beneficiario] = Field(
        None, description="Dados do beneficiário"
    )
    defaults: Optional[Defaults] = Field(
        None, description="Configurações padrões para a organização"
    )

    ENTITY_TEMPLATE: ClassVar[Optional[str]] = "ORG#{orgId}"
