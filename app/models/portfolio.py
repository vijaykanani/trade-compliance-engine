from pydantic import BaseModel
from typing import Optional


class Portfolio(BaseModel):
    portfolio_id: str
    fund_name: str
    nav: float                                      # Net Asset Value
    cash: float = 0.0
    jurisdiction: str = "USA"                       # USA | EMEA | APAC
    mandate_type: str = "BALANCED"                  # EQUITY_ONLY | BOND_ONLY | BALANCED
    positions: dict[str, float] = {}                # security_id -> market value
    sector_exposure: dict[str, float] = {}          # sector -> market value
    country_exposure: dict[str, float] = {}         # country -> market value
    restricted_list: list[str] = []                 # security IDs (corporate watch/block)
    watch_list: list[str] = []                      # heightened monitoring
    approved_counterparties: list[str] = []
    locates: list[str] = []                         # securities with short-sell locate
    daily_pnl: float = 0.0
    daily_turnover: float = 0.0
    max_position_pct: float = 10.0                  # per-security limit %
    max_sector_pct: float = 25.0                    # sector concentration limit %
    max_country_pct: float = 30.0                   # country concentration limit %
    max_daily_loss: float = 1_000_000.0             # USD
    max_daily_turnover_pct: float = 20.0
    counterparty_limits: dict[str, float] = {}      # broker_id -> max exposure USD
    employee_restricted: bool = False               # personal account dealing flag
    blackout_period: bool = False                   # earnings/event blackout
    information_barrier: list[str] = []            # sectors/tickers under Chinese wall


class MarketData(BaseModel):
    security_id: str
    ticker: str
    isin: Optional[str] = None
    sector: str = "UNKNOWN"
    industry: str = "UNKNOWN"
    country: str = "USA"
    exchange: str = "NYSE"
    market_cap: float = 0.0
    avg_daily_volume: float = 0.0
    price: float = 0.0
    is_etf: bool = False
    is_derivative: bool = False
    underlying_id: Optional[str] = None
    short_interest_pct: float = 0.0
    days_to_cover: float = 0.0
