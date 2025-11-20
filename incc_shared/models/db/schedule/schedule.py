from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.schedule.base import ScheduleBase


class ScheduleModel(ScheduleBase, DynamoBaseModel):
    ENTITY_TEMPLATE = "SCHEDULE#{id}"
