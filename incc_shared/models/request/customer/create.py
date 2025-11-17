from pydantic import Field

from incc_shared.models.db.customer.base import CustomerBase


class CreateCustomerModel(CustomerBase):
    customerId: str = Field("", exclude=True)
