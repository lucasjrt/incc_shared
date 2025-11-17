from datetime import date, datetime
from typing import Any, ClassVar, Dict, List, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from incc_shared.models.helper import is_valid_ulid, utc_now_iso


class DatetimeNormalizedModel(BaseModel):
    @model_validator(mode="before")
    def convert_dates(cls, values):
        for field_name, value in values.items():
            if isinstance(value, datetime):
                values[field_name] = value.date().strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(value, date):
                values[field_name] = value.strftime("%Y-%m-%d")
        return values


class DynamoBaseModel(DatetimeNormalizedModel, BaseModel):
    """
    Base model for DynamoDB items.

    Subclasses should override these class attributes / methods to customize:
    - ENTITY_TEMPLATE: format strings using placeholders like {orgId}, {userId}
    - compute_additional_gsis(cls, values) -> Dict[str, Optional[str]]:
         return a dict of additional gsi field names -> values
    """

    # canonical key fields that commonly exist; subclasses may or may not use them
    tenant: Optional[str] = Field(None, description="PK (e.g. ORG#<id>)")
    entity: Optional[str] = Field(None, description="SK (e.g. USER#<id>)")
    orgId: str = Field(..., description="The ID this entity belongs to")

    # created/updated audit
    createdAt: Optional[str] = Field(None, description="ISO UTC timestamp")
    createdBy: Optional[str] = Field(None, description="Usuario que criou o recurso")
    updatedAt: Optional[str] = Field(None, description="ISO UTC timestamp")
    updatedBy: Optional[str] = Field(
        None, description="Usuario que atualizou o recurso"
    )

    model_config = ConfigDict(populate_by_name=True)

    # --- subclass override points ---
    # Template example: "USER#{userId}"
    ENTITY_TEMPLATE: ClassVar[Optional[str]] = None

    @classmethod
    def compute_pk(cls, values: Dict[str, Any]) -> Optional[str]:
        try:
            return f"ORG#{values['orgId']}"
        except KeyError:
            raise ValueError("orgId is expected on every entity")

    @classmethod
    def compute_sk(cls, values: Dict[str, Any]) -> Optional[str]:
        if cls.ENTITY_TEMPLATE is None:
            return values.get("entity")
        try:
            return cls.ENTITY_TEMPLATE.format(**values)
        except Exception:
            return values.get("entity")

    @classmethod
    def compute_additional_gsis(
        cls, values: Dict[str, Any]
    ) -> Dict[str, Optional[str]]:
        """
        Subclasses override to compute GSIs specific to them.
        Return mapping gsi_field_name -> value (or None to omit).
        """
        return {}

    # model-level validator runs after field validators (Pydantic v2)
    @model_validator(mode="after")
    def canonicalize_keys(self) -> "DynamoBaseModel":
        """
        Ensures tenant/entity (PK/SK) and GSIs are set according to templates
        and compute_additional_gsis. Does NOT raise for mismatches by default -
        it prefers authoritative computed values.
        """
        values = self.model_dump()  # plain dict

        # Compute tenant/entity if template provided
        computed_pk = self.__class__.compute_pk(values)
        computed_sk = self.__class__.compute_sk(values)

        # set authoritative values
        if computed_pk is not None:
            object.__setattr__(self, "tenant", computed_pk)
        if computed_sk is not None:
            object.__setattr__(self, "entity", computed_sk)

        # compute GSIs and set them on instance
        computed_gsis = self.__class__.compute_additional_gsis(values) or {}
        for gsi_field, gsi_value in computed_gsis.items():
            # only set attribute if it's defined in the model or we allow dynamic attributes.
            # We'll set it if it exists on the instance (declared) or not (setattr anyway
            # so that to_item() will include it).
            object.__setattr__(self, gsi_field, gsi_value)

        # Ensure createdAt/updatedAt exist sensibly:
        now = utc_now_iso()
        if getattr(self, "createdAt", None) is None:
            object.__setattr__(self, "createdAt", now)
        # For update: always set updatedAt to now (model creation counts as update)
        object.__setattr__(self, "updatedAt", now)
        # createdBy/updatedBy left as-is if provided (no default actor here)

        return self

    @field_validator("orgId")
    @classmethod
    def validate_orgid(cls, v: str) -> str:
        if not is_valid_ulid(v) and v != "system":
            raise ValueError("orgId must look like a ULID (26 chars) or be system")
        return v

    # convert to dict suitable for boto3 put_item (plain python types)
    def to_item(self, exclude_none: bool = True) -> Dict[str, Any]:
        d = self.model_dump()
        if exclude_none:
            d = {k: v for k, v in d.items() if v is not None}
        return d

    @classmethod
    def from_item(
        cls: Type["DynamoBaseModel"], item: Dict[str, Any]
    ) -> "DynamoBaseModel":
        """
        Construct model from DynamoDB item (plain dict). Any missing computed
        keys will be recomputed by the model validator.
        """
        return cls(**item)


# -------------------------
# Usage examples
# -------------------------
# if __name__ == "__main__":
#     # Example creating a user
#     try:
#         raw = {
#             "userId": "abc-123-def",
#             "orgId": "01FZ6Y3G0Z6Y3QWXYZABCD1234",  # 26-char ULID-ish
#             "email": "Alice@example.com",
#             "features": ["read:document", "write:document:own"],
#             "roles": ["ADMIN"],
#             "createdBy": "system-import",  # optional actor
#         }
#
#         user = UserModel(**raw)
#         print("User model:", user)
#         print("DynamoDB Item ready to put:", user.to_item())
#
#         # Example constructing from DynamoDB item
#         fetched_item = {
#             "tenant": "ORG#01FZ6Y3G0Z6Y3QWXYZABCD1234",
#             "entity": "USER#abc-123-def",
#             "userId": "abc-123-def",
#             "orgId": "01FZ6Y3G0Z6Y3QWXYZABCD1234",
#             "email": "alice@example.com",
#             "features": ["read:document"],
#             "gsi_email_pk": "EMAIL#alice@example.com",
#             "createdAt": "2024-01-01T00:00:00Z",
#         }
#         user2 = UserModel.from_item(fetched_item)
#         print("User2 rebuilt:", user2.to_item())
#
#         # Org example
#         org = OrgModel(
#             orgId="01FZ6Y3G0Z6Y3QWXYZABCD1234", name="MyOrg", createdBy="admin"
#         )
#         print("Org item:", org.to_item())
#
#     except ValidationError as e:
#         print("Validation error:", e)
