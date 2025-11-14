from enum import Enum

from .email_index_user import EmailIndexUserModel
from .organization import OrganizationModel
from .user import UserModel
from .user_index_user import UserIndexUserModel


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"
