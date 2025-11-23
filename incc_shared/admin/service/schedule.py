from datetime import date

from boto3.dynamodb.conditions import Key

from incc_shared.admin.storage import list_dynamo_items
from incc_shared.models.db.indexes.schedule import ScheduleIndexModel
from incc_shared.service.utils import format_date


def list_schedules_for_date(target_date: date):
    condition = Key("proximaExecucao").eq(format_date(target_date))
    return list_dynamo_items(condition, ScheduleIndexModel, index_name="schedule_index")
