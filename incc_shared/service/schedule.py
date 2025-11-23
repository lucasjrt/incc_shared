from datetime import date

from boto3.dynamodb.conditions import Key
from ulid import ULID

from incc_shared.constants import EntityType
from incc_shared.models.db.indexes.schedule import ScheduleIndexModel
from incc_shared.models.db.schedule.schedule import ScheduleModel
from incc_shared.models.request.schedule.create import CreateScheduleModel
from incc_shared.models.request.schedule.update import UpdateScheduleModel
from incc_shared.service import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
    list_dynamo_items,
    update_dynamo_item,
)
from incc_shared.service.utils import format_date


def get_schedule(org_id: ULID, schedule_id: ULID):
    key = get_dynamo_key(org_id, EntityType.schedule, schedule_id)
    return get_dynamo_item(key, ScheduleModel)


def list_schedules(org_id: ULID):
    return list_dynamo_entity(org_id, EntityType.schedule, ScheduleModel)


def create_schedule(org_id: ULID, schedule: CreateScheduleModel):
    scheduleId = ULID()
    model = schedule.model_dump()
    item = ScheduleModel(
        orgId=org_id,
        id=scheduleId,
        proximaExecucao=schedule.dataInicio,
        **model,
    )

    create_dynamo_item(item.to_item())
    return scheduleId


def update_schedule(org_id: ULID, schedule_id: ULID, to_update: UpdateScheduleModel):
    key = get_dynamo_key(org_id, EntityType.schedule, schedule_id)
    return update_dynamo_item(key, to_update.to_item())


def delete_schedule(org_id: ULID, schedule_id: ULID):
    key = get_dynamo_key(org_id, EntityType.schedule, schedule_id)
    delete_dynamo_item(key)


def list_schedules_for_date(target_date: date):
    condition = Key("proximaExecucao").eq(format_date(target_date))
    return list_dynamo_items(condition, ScheduleIndexModel, index_name="schedule_index")
