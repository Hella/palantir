from dataclasses import dataclass


CoinId = str


Price = float


Timestamp = int


@dataclass
class Position:
    owner: str
    owed_token: str
    held_token: str
    collateral_token: str
    collateral: float
    principal: float
    allowance: float
    interest_rate: float
