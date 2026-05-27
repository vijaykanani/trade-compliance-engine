"""
Mock portfolio & market data service.
In production, replace with calls to your OMS / risk system / market data vendor.
"""
from app.models.portfolio import Portfolio, MarketData


DEMO_PORTFOLIOS: dict[str, Portfolio] = {
    "FUND-USA-01": Portfolio(
        portfolio_id="FUND-USA-01",
        fund_name="Global Equity Fund",
        nav=50_000_000,
        cash=5_000_000,
        jurisdiction="USA",
        mandate_type="EQUITY_ONLY",
        positions={"AAPL": 3_000_000, "MSFT": 2_500_000, "GOOGL": 1_800_000},
        sector_exposure={"Technology": 7_300_000, "Healthcare": 1_200_000},
        country_exposure={"USA": 8_500_000},
        restricted_list=["ENRN", "WCOM"],
        watch_list=["GME", "AMC"],
        locates=["TSLA", "NVDA"],
        approved_counterparties=["GOLDMAN", "MORGAN_STANLEY", "JPMORGAN"],
        daily_pnl=-120_000,
        daily_turnover=800_000,
        max_position_pct=10.0,
        max_sector_pct=25.0,
        max_daily_loss=500_000,
    ),
    "FUND-EMEA-01": Portfolio(
        portfolio_id="FUND-EMEA-01",
        fund_name="European UCITS Equity Fund",
        nav=80_000_000,
        cash=3_000_000,
        jurisdiction="EMEA",
        mandate_type="EQUITY_ONLY",
        positions={"VOW3": 2_000_000, "ASML": 3_500_000},
        sector_exposure={"Automotive": 2_000_000, "Semiconductors": 3_500_000},
        country_exposure={"DE": 2_000_000, "NL": 3_500_000},
        restricted_list=[],
        watch_list=["BARC"],
        locates=[],
        approved_counterparties=["DB", "UBS", "HSBC"],
        daily_pnl=50_000,
        daily_turnover=400_000,
        max_position_pct=5.0,
        max_sector_pct=25.0,
        max_daily_loss=1_000_000,
    ),
    "FUND-BOND-01": Portfolio(
        portfolio_id="FUND-BOND-01",
        fund_name="Fixed Income Fund",
        nav=30_000_000,
        cash=2_000_000,
        jurisdiction="USA",
        mandate_type="BOND_ONLY",
        positions={"US10Y": 5_000_000, "CORP_AAA": 4_000_000},
        sector_exposure={"Government": 5_000_000, "Corporate IG": 4_000_000},
        country_exposure={"USA": 9_000_000},
        restricted_list=[],
        watch_list=[],
        locates=[],
        approved_counterparties=["GOLDMAN", "CITI", "BARCLAYS"],
        daily_pnl=0,
        daily_turnover=100_000,
        max_position_pct=15.0,
        max_sector_pct=40.0,
        max_daily_loss=200_000,
    ),
}

DEMO_MARKET_DATA: dict[str, MarketData] = {
    "AAPL":  MarketData(security_id="AAPL",  ticker="AAPL",  isin="US0378331005", sector="Technology", industry="Consumer Electronics", country="USA", exchange="NASDAQ", market_cap=2_800_000_000_000, avg_daily_volume=80_000_000, price=185.0),
    "MSFT":  MarketData(security_id="MSFT",  ticker="MSFT",  isin="US5949181045", sector="Technology", industry="Software", country="USA", exchange="NASDAQ", market_cap=3_100_000_000_000, avg_daily_volume=25_000_000, price=415.0),
    "GOOGL": MarketData(security_id="GOOGL", ticker="GOOGL", isin="US02079K3059", sector="Technology", industry="Internet Services", country="USA", exchange="NASDAQ", market_cap=2_100_000_000_000, avg_daily_volume=20_000_000, price=175.0),
    "TSLA":  MarketData(security_id="TSLA",  ticker="TSLA",  isin="US88160R1014", sector="Automotive", industry="Electric Vehicles", country="USA", exchange="NASDAQ", market_cap=700_000_000_000,   avg_daily_volume=120_000_000, price=220.0, short_interest_pct=3.5),
    "GME":   MarketData(security_id="GME",   ticker="GME",   isin="US36467W1099", sector="Consumer Discretionary", industry="Gaming Retail", country="USA", exchange="NYSE", market_cap=5_000_000_000, avg_daily_volume=5_000_000, price=15.0, short_interest_pct=20.0),
    "NVDA":  MarketData(security_id="NVDA",  ticker="NVDA",  isin="US67066G1040", sector="Technology", industry="Semiconductors", country="USA", exchange="NASDAQ", market_cap=3_300_000_000_000, avg_daily_volume=50_000_000, price=880.0),
    "VOW3":  MarketData(security_id="VOW3",  ticker="VOW3",  isin="DE0007664039", sector="Automotive", industry="Automobiles", country="DE", exchange="XETRA", market_cap=60_000_000_000, avg_daily_volume=2_000_000, price=110.0),
    "ASML":  MarketData(security_id="ASML",  ticker="ASML",  isin="NL0010273215", sector="Semiconductors", industry="Semiconductor Equipment", country="NL", exchange="AEX", market_cap=350_000_000_000, avg_daily_volume=900_000, price=850.0),
    "BARC":  MarketData(security_id="BARC",  ticker="BARC",  isin="GB0031348658", sector="Financials", industry="Banking", country="GB", exchange="LSE", market_cap=35_000_000_000, avg_daily_volume=50_000_000, price=2.10),
}


async def get_portfolio(portfolio_id: str) -> Portfolio:
    if portfolio_id in DEMO_PORTFOLIOS:
        return DEMO_PORTFOLIOS[portfolio_id]
    # Default demo portfolio
    return Portfolio(
        portfolio_id=portfolio_id,
        fund_name=f"Portfolio {portfolio_id}",
        nav=10_000_000,
        cash=1_000_000,
        jurisdiction="USA",
        mandate_type="BALANCED",
    )


async def get_market_data(security_id: str) -> MarketData:
    if security_id in DEMO_MARKET_DATA:
        return DEMO_MARKET_DATA[security_id]
    return MarketData(security_id=security_id, ticker=security_id)
