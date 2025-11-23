from datetime import datetime
from typing import Any, ClassVar, Dict, Optional, Type

from pydantic import BaseModel, ConfigDict, Field, model_validator
from ulid import ULID


class DynamoSerializableModel(BaseModel):
    def to_item(self, exclude_none: bool = True) -> Dict[str, Any]:
        return self.model_dump(mode="json", exclude_none=exclude_none)

    @classmethod
    def from_item(
        cls: Type["DynamoSerializableModel"], item: Dict[str, Any]
    ) -> "DynamoSerializableModel":
        return cls(**item)


class DynamoBaseModel(DynamoSerializableModel):
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
    orgId: ULID = Field(..., description="The ID this entity belongs to")

    # created/updated audit
    createdAt: Optional[datetime] = Field(None, description="ISO UTC timestamp")
    createdBy: Optional[str] = Field(None, description="Entidade que criou o recurso")
    updatedAt: Optional[datetime] = Field(None, description="ISO UTC timestamp")
    updatedBy: Optional[str] = Field(
        None, description="Entidade que atualizou o recurso"
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

    # model-level validator runs after field validators
    @model_validator(mode="after")
    def canonicalize_keys(self) -> "DynamoBaseModel":
        """
        Ensures tenant/entity (PK/SK) and GSIs are set according to templates
        and compute_additional_gsis. Does NOT raise for mismatches by default -
        it prefers authoritative computed values.
        """
        values = self.model_dump()

        # Compute tenant/entity if template provided
        computed_pk = self.__class__.compute_pk(values)
        computed_sk = self.__class__.compute_sk(values)
        self.tenant = computed_pk
        self.entity = computed_sk

        # compute GSIs and set them on instance
        computed_gsis = self.__class__.compute_additional_gsis(values) or {}
        for gsi_field, gsi_value in computed_gsis.items():
            # only set attribute if it's defined in the model or we allow dynamic attributes.
            # We'll set it if it exists on the instance (declared) or not (setattr anyway
            # so that to_item() will include it).
            object.__setattr__(self, gsi_field, gsi_value)

        return self
