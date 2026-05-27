"""
Post-Trade Compliance Engine.

Runs after trade execution to detect breaches, late reporting,
wash trades, and P&L stops.
"""
import logging
from app.models.trade import ExecutedTrade
from app.models.portfolio import Portfolio, MarketData
from app.models.compliance import ComplianceResult, CheckStatus, Violation, Severity
from app.engines.decision_rules_client import DecisionRulesClient
from app.engines.rule_sets import corporate, usa, emea
from app.config import get_settings

logger = logging.getLogger(__name__)


def _build_context(trade: ExecutedTrade, portfolio: Portfolio, market_data: MarketData) -> dict:
    nav = portfolio.nav or 1
    return {
        "order_id": trade.order_id,
        "portfolio_id": trade.portfolio_id,
        "security_id": trade.security_id,
        "ticker": trade.ticker,
        "asset_class": trade.asset_class.value,
        "side": trade.side.value,
        "quantity": trade.quantity,
        "execution_price": trade.execution_price,
        "trade_value": trade.trade_value,
        "broker_id": trade.broker_id,
        "nav": nav,
        "daily_pnl": portfolio.daily_pnl,
        "daily_turnover": portfolio.daily_turnover,
        "sector": market_data.sector,
        "country": market_data.country,
        "market_cap": market_data.market_cap,
    }


async def run_post_trade_check(
    trade: ExecutedTrade,
    portfolio: Portfolio,
    market_data: MarketData,
    extra_ctx: dict | None = None,
) -> ComplianceResult:
    settings = get_settings()
    ctx = _build_context(trade, portfolio, market_data)
    if extra_ctx:
        ctx.update(extra_ctx)

    # ── 1. Try DecisionRules.io ───────────────────────────────────────────────
    if settings.decision_rules_configured:
        client = DecisionRulesClient()
        jurisdiction = trade.fund_jurisdiction.upper()

        rule_map = {
            "CORPORATE": settings.dr_rule_id_post_trade_corporate,
            "USA":       settings.dr_rule_id_post_trade_usa,
            "EMEA":      settings.dr_rule_id_post_trade_emea,
        }
        rule_id = rule_map.get(jurisdiction, settings.dr_rule_id_post_trade_corporate)
        dr_results = await client.solve(rule_id, ctx)

        if dr_results:
            from app.engines.pre_trade import _parse_decision_rules_response  # noqa: PLC0415
            result = _parse_decision_rules_response(dr_results, trade.order_id, trade.portfolio_id)
            if result:
                result.rule_source = "DECISION_RULES"
                return result
        logger.warning("DecisionRules returned empty for post-trade; falling back.")

    # ── 2. Local Rule Evaluation ──────────────────────────────────────────────
    all_violations: list[Violation] = []
    checked_rules: list[str] = []

    corp_violations = corporate.check_post_trade(trade, portfolio, ctx)
    all_violations.extend(corp_violations)
    checked_rules.extend(v.rule_id for v in corp_violations)

    jurisdiction = trade.fund_jurisdiction.upper()
    if jurisdiction == "USA":
        reg_violations = usa.check_post_trade(trade, portfolio, market_data, ctx)
    elif jurisdiction == "EMEA":
        reg_violations = emea.check_post_trade(trade, portfolio, market_data, ctx)
    else:
        reg_violations = (
            usa.check_post_trade(trade, portfolio, market_data, ctx)
            + emea.check_post_trade(trade, portfolio, market_data, ctx)
        )

    all_violations.extend(reg_violations)
    checked_rules.extend(v.rule_id for v in reg_violations)

    blocks = [v for v in all_violations if v.severity == Severity.BLOCK]
    warns  = [v for v in all_violations if v.severity == Severity.WARNING]
    passed = len(blocks) == 0

    return ComplianceResult(
        order_id=trade.order_id,
        portfolio_id=trade.portfolio_id,
        passed=passed,
        status=CheckStatus.APPROVED if passed else CheckStatus.BLOCKED,
        violations=blocks,
        warnings=warns,
        checked_rules=checked_rules,
        rule_source="LOCAL",
    )
