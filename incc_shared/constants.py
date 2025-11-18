from enum import Enum


class EntityType(str, Enum):
    organization = "ORG"
    user = "USER"
    customer = "CUSTOMER"
    boleto = "BOLETO"
    schedule = "SCHEDULE"
