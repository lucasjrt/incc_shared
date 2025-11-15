from enum import Enum


class TipoDocumento(str, Enum):
    CPF = "CPF"
    CNPJ = "CNPJ"


class TipoJuros(str, Enum):
    taxa = "TAXA"
    fixa = "FIXO"
    isenta = "ISENTO"
