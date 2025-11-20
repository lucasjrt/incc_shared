from datetime import date, datetime
from enum import Enum
from typing import Optional

from pydantic import Field, model_validator
from ulid import ULID

from incc_shared.models import ConstrainedMoney
from incc_shared.models.base import DynamoSerializableModel


class ScheduleType(str, Enum):
    parcela = "PARCELA"
    balao = "BALAO"


class ScheduleBase(DynamoSerializableModel):
    id: ULID
    valorBase: ConstrainedMoney = Field(..., description="O valor base de cada parcela")
    pagador: ULID
    vencimento: date = Field(
        ...,
        description="Primeiro vencimento. Os seguintes serão computados com base neste",
    )
    parcelas: int = Field(
        ...,
        ge=1,
        le=420,
        description="Número total de boletos que serão gerados",
    )
    dataInicio: date = Field(
        default_factory=date.today,
        description="Data em que o primeiro boleto será emitido. Os seguintes serão computados com base neste",
    )
    intervaloParcelas: int = Field(
        1, ge=1, description="Intervalo entre parcelas. Útil em balões"
    )
    ativo: bool = True
    ultimaExecucao: Optional[datetime] = None

    @model_validator(mode="after")
    def valida_datas(self) -> "ScheduleBase":
        if self.dataInicio > self.vencimento:
            raise ValueError("dataInicio deve ser antes que vencimento")
        return self
