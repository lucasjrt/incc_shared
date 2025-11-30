from typing import Any, Dict, Optional

from pydantic import ValidationError

from incc_shared.auth.context import get_context_entity
from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.schedule.base import ScheduleBase


class ScheduleModel(ScheduleBase, DynamoBaseModel):
    ENTITY_TEMPLATE = "SCHEDULE#{id}"
    gsi_org_sk: Optional[str] = None

    @classmethod
    def compute_additional_gsis(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        # TODO: This might cause issues if user is an admin acting on another org
        org_id = values.get("orgId", get_context_entity().orgId)
        if not org_id:
            raise ValidationError("Every item must have org id")

        result: Dict[str, Optional[str]] = {}
        result["gsi_org_sk"] = f"ORG#{org_id}"
        return result
