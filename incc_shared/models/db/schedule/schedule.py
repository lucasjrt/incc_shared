from typing import Any, Dict, Optional

from pydantic import ValidationError

from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.schedule.base import ScheduleBase


class ScheduleModel(ScheduleBase, DynamoBaseModel):
    ENTITY_TEMPLATE = "SCHEDULE#{id}"

    @classmethod
    def compute_additional_gsis(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        org_id = values.get("orgId")
        if not org_id:
            raise ValidationError("Every item must have org id")

        result: Dict[str, Optional[str]] = {}
        result["gsi_org_sk"] = f"ORG#{org_id}"
        return result
