from incc_shared.models.base import DynamoBaseModel
from incc_shared.models.db.customer.base import CustomerBase


class CustomerModel(CustomerBase, DynamoBaseModel):
    ENTITY_TEMPLATE = "CUSTOMER#{customerId}"
