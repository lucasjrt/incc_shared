from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.schedule.schedule import ScheduleModel
from incc_shared.models.request.schedule.create import CreateScheduleModel
from incc_shared.models.request.schedule.update import UpdateScheduleModel
from incc_shared.service import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_items,
    update_dynamo_item,
)


def get_schedule(orgId: ULID, scheduleId: ULID):
    key = get_dynamo_key(orgId, EntityType.schedule, scheduleId)
    return get_dynamo_item(key, ScheduleModel)


def list_schedules(orgId: ULID):
    return list_dynamo_items(orgId, EntityType.schedule, ScheduleModel)


def create_schedule(orgId: ULID, schedule: CreateScheduleModel):
    scheduleId = ULID()
    model = schedule.model_dump()
    item = ScheduleModel(orgId=orgId, id=scheduleId, **model)

    create_dynamo_item(item.to_item())
    return scheduleId


def update_schedule(orgId: ULID, scheduleId: ULID, to_update: UpdateScheduleModel):
    key = get_dynamo_key(orgId, EntityType.schedule, scheduleId)
    return update_dynamo_item(key, to_update.to_item())


def delete_schedule(orgId: ULID, scheduleId: ULID):
    key = get_dynamo_key(orgId, EntityType.schedule, scheduleId)
    delete_dynamo_item(key)
