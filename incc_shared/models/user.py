from enum import Enum
from typing import Any, ClassVar, Dict, List, Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.helper import COGNITO_SUB_RE, FEATURE_RE


class Feature(BaseModel):
    action: str
    resource: str
    modifier: Optional[str] = None

    @classmethod
    def from_string(cls, s: str):
        parts = s.split(":")
        if len(parts) < 2 or len(parts) > 3:
            raise ValueError(
                "Invalid feature format, expected action:resource[:modifier]"
            )
        action, resource = parts[0], parts[1]
        modifier = parts[2] if len(parts) == 3 else None
        return cls(action=action, resource=resource, modifier=modifier)

    def to_string(self) -> str:
        if self.modifier:
            return f"{self.action}:{self.resource}:{self.modifier}"
        return f"{self.action}:{self.resource}"


class Role(str, Enum):
    ADMIN = "ADMIN"
    USER = "USER"


class UserModel(DynamoBaseModel):
    userId: str = Field(..., description="Cognito username")
    email: EmailStr

    features: List[str] = Field(
        default_factory=list, description="Feature in format action:resource[:modifier]"
    )
    roles: List[Role] = Field(default_factory=lambda: [Role.USER])

    gsi_email_pk: Optional[str] = None  # GSI1 PK
    gsi_user_pk: Optional[str] = None  # GSI2 PK
    gsi_user_sk: Optional[str] = None  # GSI1/GSI2 SK

    ENTITY_TEMPLATE: ClassVar[Optional[str]] = "USER#{userId}"

    GSI_FIELD_NAMES: ClassVar[List[str]] = [
        "gsi_email_pk",
        "gsi_user_pk",
        "gsi_user_sk",
    ]

    @field_validator("userId")
    @classmethod
    def validate_userid(cls, v: str) -> str:
        if not COGNITO_SUB_RE.match(v):
            raise ValueError("userId contains invalid characters")
        return v

    @field_validator("features", mode="before")
    @classmethod
    def validate_features_list(cls, v):
        """
        Accept either list[str] or list[Feature] or list of string-like. Validate items.
        """
        if v is None:
            return []

        if not isinstance(v, list):
            raise ValueError("features must be a list")

        # normalize Feature instances to strings
        out = []
        for item in v:
            if isinstance(item, Feature):
                out.append(item.to_string())
            elif isinstance(item, str):
                if not FEATURE_RE.match(item):
                    raise ValueError(
                        f"feature '{item}' is invalid. Expect action:resource[:modifier]"
                    )
                out.append(item)
            else:
                raise ValueError("features must be Feature or str")
        return out

    @classmethod
    def compute_additional_gsis(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        """
        Compute the GSIs for UserModel. This is intentionally a classmethod so each
        subclass can implement its own logic.
        """
        email = values.get("email")
        user_id = values.get("userId")
        org_id = values.get("orgId")

        result: Dict[str, Optional[str]] = {}
        result["gsi_email_pk"] = f"EMAIL#{email.lower()}" if email else None
        result["gsi_user_pk"] = f"USER#{user_id}" if user_id else None
        result["gsi_user_sk"] = f"ORG#{org_id}" if org_id else None
        return result
