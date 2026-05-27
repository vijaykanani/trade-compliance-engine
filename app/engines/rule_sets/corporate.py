"""
Corporate Restriction Rules (firm-wide, jurisdiction-agnostic).

Covers:
- Restricted / Watch list
- Employee personal account dealing
- Blackout periods (earnings, M&A, etc.)
- Information barriers / Chinese walls
- Mandate compliance (equity-only, bond-only)
- Single-issuer concentration
- Counterparty / broker limits
- Short-sell locate requirements
- Wash trade detection
- Daily P&L hard stop
"""
from app.models.trade import TradeOrder, ExecutedTrade, OrderSide, AssetClass
from app.models.portfolio import Portfolio
from app.models.compliance import Violation, Severity, RuleJurisdiction


J = RuleJurisdiction.CORPORATE


def check_pre_trade(order: TradeOrder, portfolio: Portfolio, ctx: dict) -> list[Violation]:
    violations: list[Violation] = []
    nav = portfolio.nav or 1
    trade_value = order.quantity * order.price

    # ── CORP-001 Restricted List ─────────────────────────────────────────────
    if order.security_id in portfolio.restricted_list or order.ticker in portfolio.restricted_list:
        violations.append(Violation(
            rule_id="CORP-001", rule_name="Restricted Securities List",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"{order.ticker} is on the firm's restricted list. Trade blocked.",
            regulation_ref="Internal Policy – Restricted List",
        ))

    # ── CORP-002 Watch List (heightened monitoring) ──────────────────────────
    if order.security_id in portfolio.watch_list or order.ticker in portfolio.watch_list:
        violations.append(Violation(
            rule_id="CORP-002", rule_name="Watch List – Heightened Monitoring",
            jurisdiction=J, severity=Severity.WARNING,
            message=f"{order.ticker} is on the watch list. Requires compliance officer pre-approval.",
            regulation_ref="Internal Policy – Watch List",
        ))

    # ── CORP-003 Blackout Period ─────────────────────────────────────────────
    if portfolio.blackout_period:
        violations.append(Violation(
            rule_id="CORP-003", rule_name="Blackout Period",
            jurisdiction=J, severity=Severity.BLOCK,
            message="Trading is prohibited during the active blackout period (e.g. earnings, M&A event).",
            regulation_ref="Internal Policy – Blackout Period",
        ))

    # ── CORP-004 Employee Personal Account Dealing ───────────────────────────
    if portfolio.employee_restricted:
        violations.append(Violation(
            rule_id="CORP-004", rule_name="Employee Personal Account Dealing Restriction",
            jurisdiction=J, severity=Severity.BLOCK,
            message="Personal account dealing is restricted for this employee account. Pre-clearance required.",
            regulation_ref="Internal Policy – Personal Account Dealing",
        ))

    # ── CORP-005 Information Barrier / Chinese Wall ──────────────────────────
    if order.ticker in portfolio.information_barrier or order.security_id in portfolio.information_barrier:
        violations.append(Violation(
            rule_id="CORP-005", rule_name="Information Barrier (Chinese Wall)",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"{order.ticker} is behind an information barrier. Trade requires Chinese wall clearance.",
            regulation_ref="Internal Policy – Information Barrier",
        ))

    # ── CORP-006 Mandate Compliance – Equity Only ────────────────────────────
    if portfolio.mandate_type == "BOND_ONLY" and order.asset_class == AssetClass.EQUITY:
        violations.append(Violation(
            rule_id="CORP-006", rule_name="Mandate Breach – Bond-Only Fund",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"Fund mandate is BOND_ONLY. Equity trade in {order.ticker} is not permitted.",
            regulation_ref="Fund Mandate / Prospectus",
        ))

    if portfolio.mandate_type == "EQUITY_ONLY" and order.asset_class == AssetClass.BOND:
        violations.append(Violation(
            rule_id="CORP-007", rule_name="Mandate Breach – Equity-Only Fund",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"Fund mandate is EQUITY_ONLY. Bond trade in {order.ticker} is not permitted.",
            regulation_ref="Fund Mandate / Prospectus",
        ))

    # ── CORP-008 Single Issuer Position Limit ────────────────────────────────
    current_val = portfolio.positions.get(order.security_id, 0.0)
    projected_val = current_val + trade_value if order.side in (OrderSide.BUY, OrderSide.COVER) else current_val - trade_value
    projected_pct = (projected_val / nav) * 100

    if projected_pct > portfolio.max_position_pct:
        violations.append(Violation(
            rule_id="CORP-008", rule_name="Single Issuer Position Limit",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"{order.ticker} would reach {projected_pct:.2f}% of NAV, "
                     f"exceeding the {portfolio.max_position_pct:.0f}% limit."),
            metric_value=round(projected_pct, 2),
            threshold=portfolio.max_position_pct,
            regulation_ref="Internal Risk Policy",
        ))

    # ── CORP-009 Sector Concentration ────────────────────────────────────────
    sector = ctx.get("sector", "UNKNOWN")
    sector_val = portfolio.sector_exposure.get(sector, 0.0) + trade_value
    sector_pct = (sector_val / nav) * 100

    if sector_pct > portfolio.max_sector_pct:
        violations.append(Violation(
            rule_id="CORP-009", rule_name="Sector Concentration Limit",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"Sector '{sector}' would reach {sector_pct:.2f}% of NAV, "
                     f"exceeding the {portfolio.max_sector_pct:.0f}% limit."),
            metric_value=round(sector_pct, 2),
            threshold=portfolio.max_sector_pct,
            regulation_ref="Internal Risk Policy",
        ))

    # ── CORP-010 Short Sell Without Locate ───────────────────────────────────
    if order.side == OrderSide.SHORT and order.security_id not in portfolio.locates:
        violations.append(Violation(
            rule_id="CORP-010", rule_name="Short Sell Without Locate",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"Short sale of {order.ticker} requires a valid stock locate. No locate on file.",
            regulation_ref="Reg SHO Rule 203 / Internal Policy",
        ))

    # ── CORP-011 Unapproved Counterparty (if broker specified) ───────────────
    broker = ctx.get("broker_id")
    if broker and portfolio.approved_counterparties and broker not in portfolio.approved_counterparties:
        violations.append(Violation(
            rule_id="CORP-011", rule_name="Unapproved Counterparty / Broker",
            jurisdiction=J, severity=Severity.BLOCK,
            message=f"Broker '{broker}' is not on the approved counterparty list.",
            regulation_ref="Internal Counterparty Policy",
        ))

    # ── CORP-012 Daily Turnover Warning ──────────────────────────────────────
    projected_turnover_pct = ((portfolio.daily_turnover + trade_value) / nav) * 100
    if projected_turnover_pct > portfolio.max_daily_turnover_pct:
        violations.append(Violation(
            rule_id="CORP-012", rule_name="Daily Turnover Limit Warning",
            jurisdiction=J, severity=Severity.WARNING,
            message=(f"Daily turnover would reach {projected_turnover_pct:.2f}% of NAV, "
                     f"exceeding the {portfolio.max_daily_turnover_pct:.0f}% threshold."),
            metric_value=round(projected_turnover_pct, 2),
            threshold=portfolio.max_daily_turnover_pct,
            regulation_ref="Internal Trading Policy",
        ))

    return violations


def check_post_trade(trade: ExecutedTrade, portfolio: Portfolio, ctx: dict) -> list[Violation]:
    violations: list[Violation] = []
    nav = portfolio.nav or 1

    # ── CORP-PT-001 Daily P&L Hard Stop ──────────────────────────────────────
    if portfolio.daily_pnl < -abs(portfolio.max_daily_loss):
        violations.append(Violation(
            rule_id="CORP-PT-001", rule_name="Daily P&L Hard Stop",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"Daily loss of ${abs(portfolio.daily_pnl):,.0f} exceeds the "
                     f"${portfolio.max_daily_loss:,.0f} hard stop limit."),
            metric_value=portfolio.daily_pnl,
            threshold=-portfolio.max_daily_loss,
            regulation_ref="Internal Risk Policy",
        ))

    # ── CORP-PT-002 Wash Trade Detection ─────────────────────────────────────
    recent_opposite = ctx.get("recent_opposite_trade")
    if recent_opposite:
        violations.append(Violation(
            rule_id="CORP-PT-002", rule_name="Wash Trade Detection",
            jurisdiction=J, severity=Severity.WARNING,
            message=(f"Potential wash trade: {trade.ticker} was traded in the opposite direction "
                     f"within the same day (order {recent_opposite})."),
            regulation_ref="SEC Rule 10b-5 / Internal Policy",
        ))

    # ── CORP-PT-003 Post-Trade Position Breach ────────────────────────────────
    post_val = portfolio.positions.get(trade.security_id, 0.0) + trade.trade_value
    post_pct = (post_val / nav) * 100
    if post_pct > portfolio.max_position_pct:
        violations.append(Violation(
            rule_id="CORP-PT-003", rule_name="Post-Trade Position Limit Breach",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"{trade.ticker} position reached {post_pct:.2f}% of NAV post-execution, "
                     f"breaching the {portfolio.max_position_pct:.0f}% limit."),
            metric_value=round(post_pct, 2),
            threshold=portfolio.max_position_pct,
            regulation_ref="Internal Risk Policy",
        ))

    return violations
