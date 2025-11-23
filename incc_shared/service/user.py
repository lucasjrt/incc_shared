import boto3
from boto3.dynamodb.conditions import Key
from mypy_boto3_cognito_idp.type_defs import AdminCreateUserResponseTypeDef
from pydantic import EmailStr
from ulid import ULID

from incc_shared.auth.constants import get_cognito_pool_id
from incc_shared.auth.context import get_context_entity
from incc_shared.constants import EntityType
from incc_shared.exceptions.errors import InvalidState, PermissionDenied
from incc_shared.exceptions.http import Conflict
from incc_shared.models.db.indexes import UserIndexModel
from incc_shared.models.db.indexes.email_index import EmailIndexModel
from incc_shared.models.db.user import UserModel
from incc_shared.models.feature import Feature, Resource, Scope
from incc_shared.models.request.user.create import CreateUserModel
from incc_shared.service import (
    create_dynamo_item,
    delete_dynamo_item,
    get_dyanmo_index_item,
    get_dynamo_item,
    get_dynamo_key,
    list_dynamo_entity,
)
from incc_shared.service.org import get_org

BASE_FEATURES = [Feature.read(Resource.org)]


def get_sub(cognito_user: AdminCreateUserResponseTypeDef):
    attrs = cognito_user.get("User", {}).get("Attributes", [])
    for attr in attrs:
        if attr.get("Name") == "sub":
            sub = attr.get("Value")
            if not sub:
                raise InvalidState(f"Issue while getting id for user {cognito_user}")
            return sub


def validate_create_permission(org_id: ULID):
    creator = get_context_entity()
    if not creator:
        raise PermissionDenied("No entity is set to creator")

    if not creator.has_permission(Feature.write(Resource.org)):
        raise PermissionDenied("No permission to create user")

    if creator.orgId != org_id and not creator.has_permission(
        Feature.write(Resource.org, Scope.all)
    ):
        raise PermissionDenied("No permission to create user in another organization")


def create_user(org_id: ULID, model: CreateUserModel):
    validate_create_permission(org_id)

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

    org = get_org(org_id)
    if not org:
        raise InvalidState("Tried to create user in an inexistent org")

    user_id = get_sub(auth_user)
    if not user_id:
        raise InvalidState(
            "Failed to get id for new user. Please fix consistency by deleting cognito user manually"
        )

    user_attr = {
        "id": user_id,
        "email": model.email,
        "orgId": org_id,
        "features": BASE_FEATURES,
    }

    user = UserModel(**user_attr)
    if not org.beneficiario:
        user.features.append(Feature.write(Resource.org))

    create_dynamo_item(user.to_item())

    return user_id


def list_users(org_id: ULID):
    return list_dynamo_entity(org_id, EntityType.user, UserModel)


def get_user(org_id: ULID, username: str):
    key = get_dynamo_key(org_id, EntityType.user, username)
    return get_dynamo_item(key, UserModel)


def get_user_by_username(username: str):
    user_key = f"USER#{username}"
    condition = Key("gsi_user_pk").eq(user_key)
    return get_dyanmo_index_item("user_index", condition, UserIndexModel)


def get_user_by_email(email: EmailStr):
    email_key = f"EMAIL#{email}"
    condition = Key("gsi_email_pk").eq(email_key)
    return get_dyanmo_index_item("email_index", condition, EmailIndexModel)


def delete_user(org_id: ULID, user_id: str):
    key = get_dynamo_key(org_id, EntityType.user, user_id)
    delete_dynamo_item(key)
