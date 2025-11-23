from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.schedule.schedule import ScheduleModel
from incc_shared.models.request.schedule.create import CreateScheduleModel
from incc_shared.models.request.schedule.update import UpdateScheduleModel
from incc_shared.service.storage.dynamodb import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
    update_dynamo_item,
)


def get_schedule(schedule_id: ULID):
    key = get_dynamo_key(EntityType.schedule, schedule_id)
    return get_dynamo_item(key, ScheduleModel)


def list_schedules():
    return list_dynamo_entity(EntityType.schedule, ScheduleModel)


def create_schedule(schedule: CreateScheduleModel):
    scheduleId = ULID()
    model = schedule.model_dump()
    item = ScheduleModel(
        id=scheduleId,
        proximaExecucao=schedule.dataInicio,
        **model,
    )

    create_dynamo_item(item.to_item())
    return scheduleId


def update_schedule(schedule_id: ULID, to_update: UpdateScheduleModel):
    key = get_dynamo_key(EntityType.schedule, schedule_id)
    return update_dynamo_item(key, to_update.to_item())


def delete_schedule(schedule_id: ULID):
    key = get_dynamo_key(EntityType.schedule, schedule_id)
    delete_dynamo_item(key)
