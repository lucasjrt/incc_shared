from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.boleto.base import BoletoBase


class BoletoModel(BoletoBase, DynamoBaseModel):
    ENTITY_TEMPLATE = "BOLETO#{nossoNumero}"
