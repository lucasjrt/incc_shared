from datetime import date
from functools import cached_property

from pydantic import ValidationError, computed_field, model_validator
from ulid import ULID

from incc_shared.models import ConstrainedMoney
from incc_shared.models.base import DynamoSerializableModel
from incc_shared.models.db.schedule.base import ScheduleStatus


class ScheduleIndexModel(DynamoSerializableModel):
    tenant: str
    entity: str

    proximaExecucao: date
    valorBase: ConstrainedMoney
    pagador: ULID
    vencimento: date
    parcelas: int
    parcelasEmitidas: int
    intervaloParcelas: int
    status: ScheduleStatus
    dataInicio: date

    @computed_field
    @cached_property
    def id(self) -> ULID:
        try:
            return ULID.from_str(self.entity.split("#")[1])
        except IndexError:
            raise ValidationError(f"Invalid entity format: {self.entity}")

    @computed_field
    @cached_property
    def orgId(self) -> ULID:
        try:
            return ULID.from_str(self.tenant.split("#")[1])
        except IndexError:
            raise ValidationError(f"Invalid tenant format: {self.tenant}")

    @model_validator(mode="after")
    def valida_schedule(self) -> "ScheduleIndexModel":
        if self.dataInicio > self.vencimento:
            raise ValueError("dataInicio deve ser antes que vencimento")
        return self
