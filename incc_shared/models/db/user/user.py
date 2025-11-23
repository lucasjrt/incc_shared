from typing import Any, ClassVar, Dict, Optional

from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.user.base import UserBase
from incc_shared.models.feature import PermissionedEntity


class UserModel(UserBase, DynamoBaseModel, PermissionedEntity):
    ENTITY_TEMPLATE: ClassVar[Optional[str]] = "USER#{id}"

    gsi_user_pk: Optional[str] = None
    gsi_email_pk: Optional[str] = None
    gsi_org_sk: Optional[str] = None

    @classmethod
    def compute_additional_gsis(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        userId = values.get("userId")
        email = values.get("email")
        org_id = values.get("orgId")

        result: Dict[str, Optional[str]] = {}
        result["gsi_user_pk"] = f"USER#{userId}" if userId else None
        result["gsi_email_pk"] = f"EMAIL#{email.lower()}" if email else None
        result["gsi_org_sk"] = f"ORG#{org_id}" if org_id else None
        return result
