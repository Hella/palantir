from dataclasses import dataclass
from typing import NewType


Account = NewType("Account", str)


Currency = NewType("Currency", str)


Price = float


PositionId = NewType("PositionId", int)


Timestamp = int


@dataclass
class Position:
    owner: Account
    owed_token: Currency
    held_token: Currency
    collateral_token: Currency
    collateral: float
    principal: float
    allowance: float
    interest_rate: float
