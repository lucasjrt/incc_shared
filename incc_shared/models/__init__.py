from decimal import Decimal
from typing import Annotated

from pydantic import condecimal

from .common import Juros, TipoDocumento, TipoJuros

ConstrainedMoney = Annotated[
    Decimal, condecimal(max_digits=12, decimal_places=2, ge=Decimal("0.01"))
]
