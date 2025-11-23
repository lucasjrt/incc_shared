from enum import Enum
from typing import List

from pydantic import EmailStr, Field, ValidationError, field_validator

from incc_shared.models.feature import Feature, PermissionedEntity
from incc_shared.models.helper import COGNITO_SUB_RE, FEATURE_RE


class Role(str, Enum):
    admin = "ADMIN"
    user = "USER"


class UserBase(PermissionedEntity):
    id: str = Field(..., description="Cognito username")
    email: EmailStr

    roles: List[Role] = [Role.user]

    @field_validator("id")
    @classmethod
    def validate_userid(cls, v: str) -> str:
        if not COGNITO_SUB_RE.match(v):
            raise ValueError(f"id {v} does not match cognito user")
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
            raise ValidationError("features must be a list")

        # normalize Feature instances to strings
        out = []
        for item in v:
            if isinstance(item, Feature):
                out.append(item)
            elif isinstance(item, str):
                if not FEATURE_RE.match(item):
                    raise ValidationError(
                        f"feature '{item}' is invalid. Expect action:resource[:modifier]"
                    )
                out.append(Feature.from_string(item))
            else:
                raise ValidationError("features must be Feature or str")
        return out
