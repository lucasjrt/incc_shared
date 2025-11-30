from datetime import date
from decimal import Decimal

from incc_shared.service.calculator import calcula_valor


def test_calculator():
    valor_base = Decimal("1000")
    data_base = date(2025, 1, 1)
    data_fim = date(2025, 6, 1)
    esperado = Decimal("1024.73")
    resultado = calcula_valor(valor_base, data_base, data_fim=data_fim)
    assert resultado == esperado


# TODO: Write tests for calcula_reajuste
