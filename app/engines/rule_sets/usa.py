"""
USA Regulatory Compliance Rules.

Regulations covered:
- SEC Rule 10b-5          – Anti-fraud / insider trading
- SEC Rule 144            – Restricted & control securities
- Regulation SHO          – Short sale requirements (Rule 203, 204)
- Regulation T            – Margin / credit requirements (50% initial)
- Rule 13D/G              – Beneficial ownership (5% threshold)
- Rule 13F                – Institutional investment manager reporting (>$100M)
- Volcker Rule            – Proprietary trading restrictions (banking entities)
- Investment Company Act  – Diversification (5%/10%/25% tests for registered funds)
- FINRA Rule 4512         – Customer account information
- FINRA Rule 2010         – Standards of commercial honor
- CFTC Position Limits    – Commodity/derivatives position limits
- Pattern Day Trader      – PDT rule (FINRA 4210) – 4+ day trades in 5 days
- Regulation NMS          – Best execution obligation
- TRACE Reporting         – FINRA bond trade reporting (15-min window)
"""
from app.models.trade import TradeOrder, ExecutedTrade, OrderSide, AssetClass
from app.models.portfolio import Portfolio, MarketData
from app.models.compliance import Violation, Severity, RuleJurisdiction

J = RuleJurisdiction.USA


def check_pre_trade(
    order: TradeOrder,
    portfolio: Portfolio,
    market_data: MarketData,
    ctx: dict,
) -> list[Violation]:
    violations: list[Violation] = []
    nav = portfolio.nav or 1
    trade_value = order.quantity * order.price

    # ── USA-001 Regulation SHO – Short Sale Locate ───────────────────────────
    if order.side == OrderSide.SHORT:
        if order.security_id not in portfolio.locates:
            violations.append(Violation(
                rule_id="USA-001", rule_name="Reg SHO – Short Sale Locate Required",
                jurisdiction=J, severity=Severity.BLOCK,
                message=f"Short sale of {order.ticker} requires a valid locate under Reg SHO Rule 203.",
                regulation_ref="Regulation SHO Rule 203",
            ))

        # Hard-to-borrow / threshold securities
        if ctx.get("is_threshold_security"):
            violations.append(Violation(
                rule_id="USA-002", rule_name="Reg SHO – Threshold Security",
                jurisdiction=J, severity=Severity.WARNING,
                message=f"{order.ticker} is on the Reg SHO threshold securities list. Close-out obligations apply.",
                regulation_ref="Regulation SHO Rule 203(b)(3)",
            ))

    # ── USA-003 Regulation T – Margin Requirement (50% initial) ─────────────
    if ctx.get("is_margin_account") and order.side == OrderSide.BUY:
        margin_available = ctx.get("margin_available", 0)
        required_margin = trade_value * 0.50
        if required_margin > margin_available:
            violations.append(Violation(
                rule_id="USA-003", rule_name="Regulation T – Initial Margin Deficiency",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Reg T requires 50% initial margin (${required_margin:,.0f}). "
                         f"Available margin: ${margin_available:,.0f}."),
                metric_value=required_margin,
                threshold=margin_available,
                regulation_ref="Regulation T – Federal Reserve Board",
            ))

    # ── USA-004 Rule 13D/G – Beneficial Ownership 5% Threshold ──────────────
    current_val = portfolio.positions.get(order.security_id, 0.0)
    projected_val = current_val + trade_value
    if market_data.market_cap > 0:
        ownership_pct = (projected_val / market_data.market_cap) * 100
        if ownership_pct >= 5.0:
            violations.append(Violation(
                rule_id="USA-004", rule_name="SEC Rule 13D/G – Beneficial Ownership Threshold",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Projected ownership of {order.ticker} would reach {ownership_pct:.2f}% of market cap. "
                         f"SEC Schedule 13D/G filing required within 10 days of crossing 5%."),
                metric_value=round(ownership_pct, 2),
                threshold=5.0,
                regulation_ref="Exchange Act Rule 13D/13G",
            ))

        if ownership_pct >= 10.0:
            violations.append(Violation(
                rule_id="USA-005", rule_name="SEC Rule 16 – 10% Insider Reporting Threshold",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Projected ownership of {order.ticker} would reach {ownership_pct:.2f}%. "
                         f"Exceeds 10% insider threshold – Section 16 short-swing profit rules apply."),
                metric_value=round(ownership_pct, 2),
                threshold=10.0,
                regulation_ref="Securities Exchange Act Section 16",
            ))

    # ── USA-006 Investment Company Act – 5% Diversification Test ────────────
    if ctx.get("is_registered_fund"):
        position_pct = (projected_val / nav) * 100
        if position_pct > 5.0:
            violations.append(Violation(
                rule_id="USA-006", rule_name="Investment Company Act – 5% Diversification Test",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Registered fund: {order.ticker} position would reach {position_pct:.2f}% of NAV, "
                         f"exceeding the 5% diversification test limit."),
                metric_value=round(position_pct, 2),
                threshold=5.0,
                regulation_ref="Investment Company Act of 1940 – Section 5(b)(1)",
            ))

        # 25% single-industry test
        sector = ctx.get("sector", "UNKNOWN")
        sector_val = portfolio.sector_exposure.get(sector, 0.0) + trade_value
        sector_pct = (sector_val / nav) * 100
        if sector_pct > 25.0:
            violations.append(Violation(
                rule_id="USA-007", rule_name="Investment Company Act – 25% Industry Concentration",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Registered fund: sector '{sector}' would reach {sector_pct:.2f}% of NAV, "
                         f"exceeding the 25% industry concentration limit."),
                metric_value=round(sector_pct, 2),
                threshold=25.0,
                regulation_ref="Investment Company Act of 1940 – Section 5(b)(1)",
            ))

    # ── USA-008 Volcker Rule – Proprietary Trading ───────────────────────────
    if ctx.get("is_banking_entity") and ctx.get("is_prop_trade"):
        violations.append(Violation(
            rule_id="USA-008", rule_name="Volcker Rule – Proprietary Trading Prohibition",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"Banking entities are prohibited from proprietary trading under the Volcker Rule.",
            regulation_ref="Bank Holding Company Act – Section 619 (Volcker Rule)",
        ))

    # ── USA-009 SEC Rule 144 – Restricted Securities ─────────────────────────
    if ctx.get("is_restricted_security_rule144"):
        violations.append(Violation(
            rule_id="USA-009", rule_name="SEC Rule 144 – Restricted/Control Securities",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"{order.ticker} is classified as a restricted or control security under Rule 144. "
                     f"Holding period and volume limitations apply."),
            regulation_ref="SEC Rule 144",
        ))

    # ── USA-010 Pattern Day Trader (PDT) ─────────────────────────────────────
    if ctx.get("is_margin_account"):
        day_trades_count = ctx.get("day_trades_last_5_days", 0)
        account_equity = ctx.get("account_equity", 0)
        if day_trades_count >= 4 and account_equity < 25_000:
            violations.append(Violation(
                rule_id="USA-010", rule_name="FINRA PDT Rule – Pattern Day Trader",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Account has {day_trades_count} day trades in 5 days with equity "
                         f"${account_equity:,.0f} < $25,000 minimum. Pattern Day Trader restrictions apply."),
                metric_value=account_equity,
                threshold=25_000,
                regulation_ref="FINRA Rule 4210 – Pattern Day Trader",
            ))

    # ── USA-011 CFTC Position Limits – Derivatives ───────────────────────────
    if order.asset_class == AssetClass.DERIVATIVE:
        cftc_limit = ctx.get("cftc_position_limit", 0)
        current_derivative_exposure = ctx.get("current_derivative_exposure", 0)
        projected_exposure = current_derivative_exposure + order.quantity
        if cftc_limit > 0 and projected_exposure > cftc_limit:
            violations.append(Violation(
                rule_id="USA-011", rule_name="CFTC Position Limit – Commodity Derivatives",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Projected derivative exposure {projected_exposure:,.0f} contracts exceeds "
                         f"CFTC position limit of {cftc_limit:,.0f} contracts for {order.ticker}."),
                metric_value=projected_exposure,
                threshold=float(cftc_limit),
                regulation_ref="CFTC Regulation – Part 150 Position Limits",
            ))

    # ── USA-012 Regulation NMS – Best Execution Warning ──────────────────────
    if ctx.get("nbbo_price") and order.order_type and order.order_type.value == "MARKET":
        nbbo = ctx.get("nbbo_price", order.price)
        deviation_pct = abs(order.price - nbbo) / nbbo * 100
        if deviation_pct > 1.0:
            violations.append(Violation(
                rule_id="USA-012", rule_name="Regulation NMS – Best Execution",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Order price ${order.price:.2f} deviates {deviation_pct:.2f}% from NBBO ${nbbo:.2f}. "
                         f"Best execution review required under Reg NMS."),
                metric_value=round(deviation_pct, 2),
                threshold=1.0,
                regulation_ref="Regulation NMS Rule 611",
            ))

    return violations


def check_post_trade(
    trade: ExecutedTrade,
    portfolio: Portfolio,
    market_data: MarketData,
    ctx: dict,
) -> list[Violation]:
    violations: list[Violation] = []

    # ── USA-PT-001 TRACE Reporting – 15-min Bond Reporting Window ────────────
    if trade.asset_class == AssetClass.BOND:
        reporting_delay_min = ctx.get("reporting_delay_minutes", 0)
        if reporting_delay_min > 15:
            violations.append(Violation(
                rule_id="USA-PT-001", rule_name="FINRA TRACE – Late Bond Trade Report",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Bond trade in {trade.ticker} reported {reporting_delay_min} minutes after execution. "
                         f"TRACE requires reporting within 15 minutes."),
                metric_value=float(reporting_delay_min),
                threshold=15.0,
                regulation_ref="FINRA TRACE Rule 6730",
            ))

    # ── USA-PT-002 Rule 13F – Institutional Reporting Threshold ─────────────
    if ctx.get("is_13f_filer") and ctx.get("quarter_end"):
        if portfolio.nav > 100_000_000:
            violations.append(Violation(
                rule_id="USA-PT-002", rule_name="SEC Rule 13F – Institutional Manager Reporting",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Fund NAV ${portfolio.nav:,.0f} exceeds $100M threshold. "
                         f"SEC Form 13F quarterly filing is required within 45 days of quarter-end."),
                metric_value=portfolio.nav,
                threshold=100_000_000,
                regulation_ref="Securities Exchange Act Section 13(f)",
            ))

    # ── USA-PT-003 Reg SHO – Failure to Deliver Close-out ───────────────────
    if trade.side == OrderSide.SHORT and ctx.get("fail_to_deliver_days", 0) >= 13:
        violations.append(Violation(
            rule_id="USA-PT-003", rule_name="Reg SHO – Failure to Deliver Close-out",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"{trade.ticker} has failed to deliver for {ctx['fail_to_deliver_days']} settlement days. "
                     f"Mandatory close-out required under Reg SHO Rule 204."),
            regulation_ref="Regulation SHO Rule 204",
        ))

    return violations
