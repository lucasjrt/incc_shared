from enum import Enum
from functools import cached_property
from typing import List, Optional, Tuple, overload

from pydantic import (
    Field,
    ValidationError,
    computed_field,
    field_serializer,
    field_validator,
)
from ulid import ULID

from incc_shared.models.base import DynamoSerializableModel


class Action(str, Enum):
    read = "read"
    write = "write"


class Resource(str, Enum):
    user = "user"
    org = "org"
    customer = "customer"
    boleto = "boleto"
    schedule = "schedule"


class Scope(str, Enum):
    org = "org"
    all = "all"

    @property
    def level(self) -> int:
        order = {
            Scope.org: 1,
            Scope.all: 2,
        }
        return order[self]

    def includes(self, required: "Scope"):
        return self.level >= required.level


class Feature(DynamoSerializableModel):
    action: Action
    resource: Resource
    scope: Optional[Scope] = None
    # modifier: Optional[str] = None # Do we ever need this?

    @classmethod
    def from_string(cls, s: str):
        parts = s.split(":")
        if len(parts) < 2:
            raise ValueError("Invalid feature format, expected action:resource[:scope]")
        action = Action(parts[0])
        resource = Resource(parts[1])
        scope = Scope(parts[2]) if len(parts) == 3 else None
        return cls(action=action, resource=resource, scope=scope)

    def to_string(self) -> str:
        if self.scope:
            return f"{self.action.value}:{self.resource.value}:{self.scope.value}"
        return f"{self.action.value}:{self.resource.value}"

    def key(self) -> Tuple[str, str, Optional[str]]:
        return (self.action, self.resource, self.scope)

    @classmethod
    def write(cls, resource: Resource, scope: Optional[Scope] = None):
        return cls(action=Action.write, resource=resource, scope=scope)

    @classmethod
    def read(cls, resource: Resource, scope: Optional[Scope] = None):
        return cls(action=Action.read, resource=resource, scope=scope)


class PermissionedEntity(DynamoSerializableModel):
    tenant: str
    features: List[Feature] = Field(
        default_factory=list,
        description="Feature list each in format action:resource[:modifier]",
    )

    @computed_field
    @cached_property
    def orgId(self) -> ULID:
        try:
            return ULID.from_str(self.tenant.split("#")[1])
        except IndexError:
            raise ValidationError("Tenant must be on format ORG#{ID}")

    @field_validator("features", mode="before")
    @classmethod
    def parse_features(cls, v):
        if isinstance(v, list) and v and isinstance(v[0], str):
            return [Feature.from_string(s) for s in v]
        return v

    @field_serializer("features")
    def serialize_features(self, features: List[Feature]):
        return [f.to_string() for f in features]

    @overload
    def has_permission(self, feature: Feature) -> bool: ...

    @overload
    def has_permission(
        self,
        action: Action,
        resource: Resource,
        scope: Optional[Scope] = ...,
    ) -> bool: ...

    def has_permission(self, *args, **kwargs) -> bool:
        if len(args) == 1 and isinstance(args[0], Feature):
            feature: Feature = args[0]
            action = feature.action
            resource = feature.resource
            required_scope = feature.scope or Scope.org
        else:
            if len(args) < 2:
                raise TypeError(
                    "has_permission expects either (Feature) or (action, resource, [scope])"
                )
            action, resource = args[0], args[1]

            # scope can come as positional or keyword
            if len(args) >= 3:
                required_scope = args[2]
            else:
                required_scope = kwargs.get("scope", Scope.org)

            if required_scope is None:
                required_scope = Scope.org

        return self._has_permission_internal(action, resource, required_scope)

    def _has_permission_internal(
        self,
        action: Action,
        resource: Resource,
        required_scope: Scope,
    ) -> bool:
        for f in getattr(self, "features", []):
            if f.action == action and f.resource == resource:
                user_scope = f.scope or Scope.org
                if user_scope.includes(required_scope):
                    return True
        return False
