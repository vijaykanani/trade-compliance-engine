"""
Pre-Trade Compliance Engine.

Strategy:
1. Try DecisionRules.io first (if API key configured).
2. Fall back to local rule sets (Corporate + jurisdiction rules).
"""
import logging
from app.models.trade import TradeOrder
from app.models.portfolio import Portfolio, MarketData
from app.models.compliance import ComplianceResult, CheckStatus, Violation, Severity
from app.engines.decision_rules_client import DecisionRulesClient
from app.engines.rule_sets import corporate, usa, emea
from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_context(order: TradeOrder, portfolio: Portfolio, market_data: MarketData) -> dict:
    """Flat context dict sent to DecisionRules.io and used by local rules."""
    nav = portfolio.nav or 1
    trade_value = order.quantity * order.price
    current_val = portfolio.positions.get(order.security_id, 0.0)
    projected_val = current_val + trade_value

    return {
        # Order fields
        "order_id": order.order_id,
        "portfolio_id": order.portfolio_id,
        "security_id": order.security_id,
        "ticker": order.ticker,
        "asset_class": order.asset_class.value,
        "side": order.side.value,
        "quantity": order.quantity,
        "price": order.price,
        "trade_value": trade_value,
        "currency": order.currency,
        "trader_id": order.trader_id,
        "jurisdiction": order.fund_jurisdiction,

        # Portfolio context
        "nav": nav,
        "current_position_value": current_val,
        "projected_position_value": projected_val,
        "projected_position_pct": round((projected_val / nav) * 100, 4),
        "daily_turnover": portfolio.daily_turnover,
        "daily_turnover_pct": round(((portfolio.daily_turnover + trade_value) / nav) * 100, 4),
        "daily_pnl": portfolio.daily_pnl,
        "mandate_type": portfolio.mandate_type,
        "blackout_period": portfolio.blackout_period,
        "employee_restricted": portfolio.employee_restricted,
        "is_restricted": (
            order.security_id in portfolio.restricted_list
            or order.ticker in portfolio.restricted_list
        ),
        "is_watch_list": (
            order.security_id in portfolio.watch_list
            or order.ticker in portfolio.watch_list
        ),
        "has_locate": order.security_id in portfolio.locates,
        "short_without_locate": (
            order.side.value == "SHORT" and order.security_id not in portfolio.locates
        ),

        # Market data context
        "sector": market_data.sector,
        "industry": market_data.industry,
        "country": market_data.country,
        "market_cap": market_data.market_cap,
        "avg_daily_volume": market_data.avg_daily_volume,
        "short_interest_pct": market_data.short_interest_pct,

        # Sector exposure
        "sector_value": portfolio.sector_exposure.get(market_data.sector, 0.0),
        "sector_pct": round(
            (portfolio.sector_exposure.get(market_data.sector, 0.0) + trade_value) / nav * 100, 4
        ),

        # Country exposure
        "country_value": portfolio.country_exposure.get(market_data.country, 0.0),
        "country_pct": round(
            (portfolio.country_exposure.get(market_data.country, 0.0) + trade_value) / nav * 100, 4
        ),
    }


def _parse_decision_rules_response(
    dr_results: list[dict],
    order_id: str,
    portfolio_id: str,
) -> ComplianceResult | None:
    """Parse DecisionRules.io response into ComplianceResult."""
    if not dr_results:
        return None

    violations, warnings, checked = [], [], []
    for item in dr_results:
        rule_id = item.get("ruleId", "DR-UNKNOWN")
        checked.append(rule_id)
        status = item.get("status", "PASS")
        if status in ("BLOCK", "FAIL"):
            violations.append(Violation(
                rule_id=rule_id,
                rule_name=item.get("ruleName", rule_id),
                jurisdiction=item.get("jurisdiction", "CORPORATE"),
                severity=Severity.BLOCK,
                message=item.get("message", "Rule breached"),
                metric_value=item.get("metricValue"),
                threshold=item.get("threshold"),
                regulation_ref=item.get("regulationRef"),
            ))
        elif status == "WARNING":
            warnings.append(Violation(
                rule_id=rule_id,
                rule_name=item.get("ruleName", rule_id),
                jurisdiction=item.get("jurisdiction", "CORPORATE"),
                severity=Severity.WARNING,
                message=item.get("message", "Warning"),
                metric_value=item.get("metricValue"),
                threshold=item.get("threshold"),
                regulation_ref=item.get("regulationRef"),
            ))

    passed = len(violations) == 0
    return ComplianceResult(
        order_id=order_id,
        portfolio_id=portfolio_id,
        passed=passed,
        status=CheckStatus.APPROVED if passed else CheckStatus.BLOCKED,
        violations=violations,
        warnings=warnings,
        checked_rules=checked,
        rule_source="DECISION_RULES",
    )


async def run_pre_trade_check(
    order: TradeOrder,
    portfolio: Portfolio,
    market_data: MarketData,
    extra_ctx: dict | None = None,
) -> ComplianceResult:
    settings = get_settings()
    ctx = _build_context(order, portfolio, market_data)
    if extra_ctx:
        ctx.update(extra_ctx)

    # ── 1. Try DecisionRules.io ───────────────────────────────────────────────
    if settings.decision_rules_configured:
        client = DecisionRulesClient()
        jurisdiction = order.fund_jurisdiction.upper()

        rule_map = {
            "CORPORATE": settings.dr_rule_id_pre_trade_corporate,
            "USA":       settings.dr_rule_id_pre_trade_usa,
            "EMEA":      settings.dr_rule_id_pre_trade_emea,
        }
        rule_id = rule_map.get(jurisdiction, settings.dr_rule_id_pre_trade_corporate)
        dr_results = await client.solve(rule_id, ctx)

        if dr_results:
            result = _parse_decision_rules_response(dr_results, order.order_id, order.portfolio_id)
            if result:
                return result
        logger.warning("DecisionRules returned empty; falling back to local rules.")

    # ── 2. Local Rule Evaluation ──────────────────────────────────────────────
    all_violations: list[Violation] = []
    checked_rules: list[str] = []

    corp_violations = corporate.check_pre_trade(order, portfolio, ctx)
    all_violations.extend(corp_violations)
    checked_rules.extend(v.rule_id for v in corp_violations)

    jurisdiction = order.fund_jurisdiction.upper()
    if jurisdiction == "USA":
        reg_violations = usa.check_pre_trade(order, portfolio, market_data, ctx)
    elif jurisdiction == "EMEA":
        reg_violations = emea.check_pre_trade(order, portfolio, market_data, ctx)
    else:
        reg_violations = (
            usa.check_pre_trade(order, portfolio, market_data, ctx)
            + emea.check_pre_trade(order, portfolio, market_data, ctx)
        )

    all_violations.extend(reg_violations)
    checked_rules.extend(v.rule_id for v in reg_violations)

    blocks = [v for v in all_violations if v.severity == Severity.BLOCK]
    warns  = [v for v in all_violations if v.severity == Severity.WARNING]
    passed = len(blocks) == 0

    return ComplianceResult(
        order_id=order.order_id,
        portfolio_id=order.portfolio_id,
        passed=passed,
        status=CheckStatus.APPROVED if passed else CheckStatus.BLOCKED,
        violations=blocks,
        warnings=warns,
        checked_rules=checked_rules,
        rule_source="LOCAL",
    )
