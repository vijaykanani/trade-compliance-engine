from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    SHORT = "SHORT"
    COVER = "COVER"          # buy-to-cover a short


class AssetClass(str, Enum):
    EQUITY = "EQUITY"
    BOND = "BOND"
    DERIVATIVE = "DERIVATIVE"
    FX = "FX"
    COMMODITY = "COMMODITY"
    ETF = "ETF"


class OrderType(str, Enum):
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"


class TradeOrder(BaseModel):
    order_id: str
    portfolio_id: str
    security_id: str
    ticker: str
    isin: Optional[str] = None
    asset_class: AssetClass
    side: OrderSide
    quantity: float = Field(gt=0)
    price: float = Field(gt=0)
    currency: str = "USD"
    order_type: OrderType = OrderType.MARKET
    trader_id: str
    fund_jurisdiction: str = "USA"       # USA | EMEA | APAC
    strategy: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ExecutedTrade(TradeOrder):
    execution_price: float
    execution_time: datetime = Field(default_factory=datetime.utcnow)
    broker_id: str
    counterparty_id: Optional[str] = None
    settlement_date: Optional[str] = None
    status: str = "EXECUTED"

    @property
    def trade_value(self) -> float:
        return self.quantity * self.execution_price
