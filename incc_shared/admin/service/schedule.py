from datetime import date

from boto3.dynamodb.conditions import Attr, Key

from incc_shared.models.db.indexes.schedule import ScheduleIndexModel
from incc_shared.models.db.schedule.base import ScheduleStatus
from incc_shared.service.storage.dynamodb import list_dynamo_items
from incc_shared.service.utils import format_date


def list_schedules_for_date(target_date: date):
    condition = Key("proximaExecucao").eq(format_date(target_date))
    filter = Attr("status").eq(ScheduleStatus.ativo.value)
    return list_dynamo_items(
        condition,
        ScheduleIndexModel,
        IndexName="schedule_index",
        FilterExpression=filter,
    )
