from typing import TYPE_CHECKING

import boto3
from boto3.dynamodb.conditions import Key
from pydantic import EmailStr

from incc_shared.auth.constants import get_cognito_pool_id
from incc_shared.auth.context import get_context_entity
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import InvalidState, PermissionDenied
from incc_shared.exceptions.http import Conflict
from incc_shared.models.db.indexes import UserIndexModel
from incc_shared.models.db.indexes.email_index import EmailIndexModel
from incc_shared.models.db.user import UserModel
from incc_shared.models.feature import Feature, Resource
from incc_shared.models.request.user.create import CreateUserModel
from incc_shared.service.organization import get_org
from incc_shared.service.storage.dynamodb import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dyanmo_index_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
)

if TYPE_CHECKING:
    from mypy_boto3_cognito_idp.type_defs import AdminCreateUserResponseTypeDef

BASE_FEATURES = [Feature.read(Resource.org)]


def get_sub(cognito_user: "AdminCreateUserResponseTypeDef"):
    attrs = cognito_user.get("User", {}).get("Attributes", [])
    for attr in attrs:
        if attr.get("Name") == "sub":
            sub = attr.get("Value")
            if not sub:
                raise InvalidState(f"Issue while getting id for user {cognito_user}")
            return sub


def create_user(model: CreateUserModel):
    creator = get_context_entity()
    if not creator.has_permission(Feature.write(Resource.org)):
        raise PermissionDenied("No permission to create user")

    if get_user_by_email(model.email):
        raise Conflict("User already exists")

    # Create Cognito user
    cognito = boto3.client("cognito-idp")
    try:
        auth_user = cognito.admin_create_user(
            UserPoolId=get_cognito_pool_id(),
            Username=model.email,
            DesiredDeliveryMediums=["EMAIL"],
        )
    except cognito.exceptions.UsernameExistsException:
        print("UNEXPECTED - User already exists in Cognito, but not in DyanamoDB")
        raise Conflict("User exists in Cognito")

    org = get_org()
    if not org:
        raise InvalidState("Tried to create user in an inexistent org")

    user_id = get_sub(auth_user)
    if not user_id:
        raise InvalidState(
            "Failed to get id for new user. Please fix consistency by deleting cognito user manually"
        )

    user_attr = {
        "tenant": f"ORG#{org.orgId}",
        "id": user_id,
        "email": model.email,
        "features": BASE_FEATURES,
    }

    user = UserModel(**user_attr)
    if not org.beneficiario:
        user.features.append(Feature.write(Resource.org))

    create_dynamo_item(user.to_item())

    return user_id


def list_users():
    return list_dynamo_entity(EntityType.user, UserModel)


def get_user(username: str):
    key = get_dynamo_key(EntityType.user, username)
    return get_dynamo_item(key, UserModel)


def get_user_by_username(username: str):
    user_key = f"USER#{username}"
    condition = Key("gsi_user_pk").eq(user_key)
    return get_dyanmo_index_item("user_index", condition, UserIndexModel)


def get_user_by_email(email: EmailStr):
    email_key = f"EMAIL#{email}"
    condition = Key("gsi_email_pk").eq(email_key)
    return get_dyanmo_index_item("email_index", condition, EmailIndexModel)


def delete_user(user_id: str):
    key = get_dynamo_key(EntityType.user, user_id)
    delete_dynamo_item(key)
