from pydantic import EmailStr

from incc_shared.models.base import DynamoSerializableModel


class CreateUserModel(DynamoSerializableModel):
    email: EmailStr
