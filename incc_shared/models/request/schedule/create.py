from datetime import date

from pydantic import Field
from ulid import ULID

from incc_shared.models.db.schedule.base import ScheduleBase


class CreateScheduleModel(ScheduleBase):
    id: ULID = Field(default_factory=ULID, exclude=True)
    proximaExecucao: date = Field(default_factory=date.today, exclude=True)
