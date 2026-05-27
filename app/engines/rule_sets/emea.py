"""
EMEA Regulatory Compliance Rules.

Regulations covered:
- MiFID II / MiFIR        – Best execution, transaction reporting, position limits (Art. 57)
- MAR                     – Market Abuse Regulation (insider trading, market manipulation, STR)
- EMIR                    – Derivatives reporting & clearing obligations
- SFTR                    – Securities Financing Transactions Regulation
- UK FCA                  – Post-Brexit FCA rules (COBS, SUP, DTR)
- ESMA Position Limits    – Commodity derivatives (MiFID II Art. 57)
- PRIIPs                  – Packaged Retail Investment Products (KID requirement)
- AIFMD                   – Alternative Investment Fund Managers Directive
- UCITS                   – Undertakings for Collective Investment in Transferable Securities
- SFDR                    – Sustainable Finance Disclosure Regulation (ESG)
- Short Selling Regulation – EU SSR (Regulation No 236/2012)
- MiFID II Article 26     – Transaction reporting to National Competent Authority (NCA)
"""
from app.models.trade import TradeOrder, ExecutedTrade, OrderSide, AssetClass
from app.models.portfolio import Portfolio, MarketData
from app.models.compliance import Violation, Severity, RuleJurisdiction

J = RuleJurisdiction.EMEA


def check_pre_trade(
    order: TradeOrder,
    portfolio: Portfolio,
    market_data: MarketData,
    ctx: dict,
) -> list[Violation]:
    violations: list[Violation] = []
    nav = portfolio.nav or 1
    trade_value = order.quantity * order.price

    # ── EMEA-001 MAR – Insider Trading / Inside Information ──────────────────
    if ctx.get("has_inside_information"):
        violations.append(Violation(
            rule_id="EMEA-001", rule_name="MAR – Inside Information / Insider Trading",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"Trading in {order.ticker} is prohibited. Firm or trader holds inside information. "
                     f"Market Abuse Regulation Article 8 applies."),
            regulation_ref="EU MAR – Article 8 (Regulation EU 596/2014)",
        ))

    # ── EMEA-002 MAR – Market Manipulation Indicators ────────────────────────
    if ctx.get("market_manipulation_flag"):
        violations.append(Violation(
            rule_id="EMEA-002", rule_name="MAR – Market Manipulation Risk",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"Order for {order.ticker} shows market manipulation indicators (e.g., layering, spoofing, "
                     f"marking the close). Blocked under MAR Article 12."),
            regulation_ref="EU MAR – Article 12 (Regulation EU 596/2014)",
        ))

    # ── EMEA-003 EU Short Selling Regulation – Net Short Position ────────────
    if order.side == OrderSide.SHORT:
        net_short_pct = ctx.get("net_short_position_pct", 0.0)
        projected_short_pct = net_short_pct + (trade_value / (market_data.market_cap or 1)) * 100

        if projected_short_pct >= 0.1:
            violations.append(Violation(
                rule_id="EMEA-003", rule_name="EU SSR – Net Short Position Notification (0.1%)",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Net short position in {order.ticker} would reach {projected_short_pct:.3f}% of issued capital. "
                         f"Notification to NCA required at 0.1% and each 0.1% increment."),
                metric_value=round(projected_short_pct, 3),
                threshold=0.1,
                regulation_ref="EU Short Selling Regulation – Art. 5 (Regulation EU 236/2012)",
            ))

        if projected_short_pct >= 0.5:
            violations.append(Violation(
                rule_id="EMEA-004", rule_name="EU SSR – Net Short Position Public Disclosure (0.5%)",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Net short position in {order.ticker} would reach {projected_short_pct:.3f}%. "
                         f"Public disclosure required at 0.5% under EU SSR Art. 6."),
                metric_value=round(projected_short_pct, 3),
                threshold=0.5,
                regulation_ref="EU Short Selling Regulation – Art. 6 (Regulation EU 236/2012)",
            ))

        # Uncovered short selling ban
        if ctx.get("is_share_not_borrowable"):
            violations.append(Violation(
                rule_id="EMEA-005", rule_name="EU SSR – Uncovered Short Sale Prohibited",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Uncovered (naked) short selling of {order.ticker} is prohibited under EU SSR. "
                         f"Shares must be borrowed or a locate confirmed."),
                regulation_ref="EU Short Selling Regulation – Art. 12 (Regulation EU 236/2012)",
            ))

    # ── EMEA-006 MiFID II Art. 57 – Commodity Derivative Position Limits ─────
    if order.asset_class in (AssetClass.DERIVATIVE, AssetClass.COMMODITY):
        esma_limit = ctx.get("esma_position_limit_contracts", 0)
        current_pos = ctx.get("current_derivative_position", 0)
        if esma_limit > 0 and (current_pos + order.quantity) > esma_limit:
            violations.append(Violation(
                rule_id="EMEA-006", rule_name="MiFID II Art. 57 – ESMA Commodity Position Limit",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Projected position {current_pos + order.quantity:,.0f} contracts in {order.ticker} "
                         f"exceeds ESMA position limit of {esma_limit:,.0f} contracts."),
                metric_value=float(current_pos + order.quantity),
                threshold=float(esma_limit),
                regulation_ref="MiFID II Article 57 / ESMA Position Limits",
            ))

    # ── EMEA-007 MiFID II – Best Execution (Art. 27) ─────────────────────────
    best_bid = ctx.get("best_bid_price")
    best_ask = ctx.get("best_ask_price")
    if best_ask and order.side == OrderSide.BUY:
        deviation = (order.price - best_ask) / best_ask * 100
        if deviation > 0.5:
            violations.append(Violation(
                rule_id="EMEA-007", rule_name="MiFID II Art. 27 – Best Execution Deviation",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Order price ${order.price:.4f} is {deviation:.2f}% above best ask ${best_ask:.4f}. "
                         f"Best execution policy review required under MiFID II Art. 27."),
                metric_value=round(deviation, 2),
                threshold=0.5,
                regulation_ref="MiFID II Article 27 – Best Execution",
            ))

    # ── EMEA-008 UCITS – 5% / 10% Single Issuer Diversification ─────────────
    if ctx.get("is_ucits_fund"):
        current_val = portfolio.positions.get(order.security_id, 0.0)
        projected_val = current_val + trade_value
        position_pct = (projected_val / nav) * 100

        if position_pct > 5.0:
            violations.append(Violation(
                rule_id="EMEA-008", rule_name="UCITS – 5% Single Issuer Limit",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"UCITS fund: {order.ticker} would reach {position_pct:.2f}% of NAV. "
                         f"UCITS rules generally restrict single-issuer exposure to 5% (up to 10% with approval)."),
                metric_value=round(position_pct, 2),
                threshold=5.0,
                regulation_ref="UCITS Directive Art. 52 (2009/65/EC)",
            ))

        # 40% bucket rule: positions between 5-10% cannot collectively exceed 40% of NAV
        concentrated_bucket = ctx.get("ucits_concentrated_bucket_pct", 0.0)
        if concentrated_bucket > 40.0:
            violations.append(Violation(
                rule_id="EMEA-009", rule_name="UCITS – 40% Bucket Rule",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"UCITS fund: 5-10% concentrated positions total {concentrated_bucket:.2f}% of NAV, "
                         f"exceeding the 40% bucket limit."),
                metric_value=round(concentrated_bucket, 2),
                threshold=40.0,
                regulation_ref="UCITS Directive Art. 52(2) (2009/65/EC)",
            ))

    # ── EMEA-010 AIFMD – Leverage Limit ──────────────────────────────────────
    if ctx.get("is_aifmd_fund"):
        leverage_ratio = ctx.get("current_leverage_ratio", 1.0)
        max_leverage = ctx.get("aifmd_max_leverage", 3.0)
        if leverage_ratio > max_leverage:
            violations.append(Violation(
                rule_id="EMEA-010", rule_name="AIFMD – Leverage Limit Breach",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"AIF leverage ratio {leverage_ratio:.2f}x would exceed the disclosed maximum "
                         f"of {max_leverage:.2f}x under AIFMD."),
                metric_value=leverage_ratio,
                threshold=max_leverage,
                regulation_ref="AIFMD Article 15 (2011/61/EU)",
            ))

    # ── EMEA-011 EMIR – Uncleared Derivative Obligation ─────────────────────
    if order.asset_class == AssetClass.DERIVATIVE:
        if ctx.get("is_emir_clearing_obligated") and not ctx.get("is_centrally_cleared"):
            violations.append(Violation(
                rule_id="EMEA-011", rule_name="EMIR – Mandatory Central Clearing Obligation",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"Derivative {order.ticker} falls under EMIR mandatory clearing obligation "
                         f"but is not routed to a central counterparty (CCP)."),
                regulation_ref="EMIR Article 4 (Regulation EU 648/2012)",
            ))

        # Bilateral margin rules for non-cleared OTC
        if not ctx.get("is_centrally_cleared") and not ctx.get("initial_margin_exchanged"):
            violations.append(Violation(
                rule_id="EMEA-012", rule_name="EMIR – Bilateral Margin Requirements",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"Non-cleared OTC derivative in {order.ticker} requires bilateral initial "
                         f"and variation margin exchange under EMIR RTS."),
                regulation_ref="EMIR RTS on Margin for Non-Cleared OTC Derivatives",
            ))

    # ── EMEA-013 UK FCA – DTR 5 Major Shareholding Disclosure ───────────────
    if market_data.country == "GB":
        current_val = portfolio.positions.get(order.security_id, 0.0)
        projected_val = current_val + trade_value
        if market_data.market_cap > 0:
            ownership_pct = (projected_val / market_data.market_cap) * 100
            if ownership_pct >= 3.0:
                violations.append(Violation(
                    rule_id="EMEA-013", rule_name="UK FCA DTR 5 – Major Shareholding Notification",
                    jurisdiction=J, severity=Severity.WARNING,
                    message=(f"Projected ownership of {order.ticker} (UK-listed) would reach {ownership_pct:.2f}%. "
                             f"FCA DTR 5 notification required at 3% and each 1% thereafter."),
                    metric_value=round(ownership_pct, 2),
                    threshold=3.0,
                    regulation_ref="UK FCA Disclosure and Transparency Rules – DTR 5",
                ))

    # ── EMEA-014 EU Transparency – Large Shareholding Notification ───────────
    if market_data.country in ("DE", "FR", "NL", "IT", "ES", "BE", "AT", "SE", "DK", "FI"):
        current_val = portfolio.positions.get(order.security_id, 0.0)
        projected_val = current_val + trade_value
        if market_data.market_cap > 0:
            ownership_pct = (projected_val / market_data.market_cap) * 100
            if ownership_pct >= 5.0:
                violations.append(Violation(
                    rule_id="EMEA-014", rule_name="EU Transparency Directive – 5% Shareholding Disclosure",
                    jurisdiction=J, severity=Severity.WARNING,
                    message=(f"Projected ownership of {order.ticker} ({market_data.country}) would reach {ownership_pct:.2f}%. "
                             f"Transparency Directive notification required at 5% (and 10%, 15%, 20%, 25%, 30%, 50%, 75%)."),
                    metric_value=round(ownership_pct, 2),
                    threshold=5.0,
                    regulation_ref="EU Transparency Directive Art. 9 (2004/109/EC)",
                ))

    # ── EMEA-015 MAR – Suspicious Transaction Reporting (STR) ────────────────
    if ctx.get("str_flag"):
        violations.append(Violation(
            rule_id="EMEA-015", rule_name="MAR – Suspicious Transaction Report (STR) Required",
            jurisdiction=J, severity=Severity.WARNING,
            message=(f"Order for {order.ticker} has been flagged as potentially suspicious. "
                     f"A Suspicious Transaction Report (STR) must be filed with the NCA under MAR Art. 16."),
            regulation_ref="EU MAR – Article 16 (Regulation EU 596/2014)",
        ))

    # ── EMEA-016 SFDR – ESG Disclosure ───────────────────────────────────────
    if ctx.get("is_sfdr_article8_or_9") and ctx.get("security_esg_score") is not None:
        esg_score = ctx.get("security_esg_score", 100)
        min_esg = ctx.get("min_esg_score_threshold", 30)
        if esg_score < min_esg:
            violations.append(Violation(
                rule_id="EMEA-016", rule_name="SFDR – ESG Score Below Fund Threshold",
                jurisdiction=J, severity=Severity.WARNING,
                message=(f"{order.ticker} ESG score {esg_score} is below the fund's minimum threshold of {min_esg} "
                         f"for SFDR Article 8/9 compliance."),
                metric_value=float(esg_score),
                threshold=float(min_esg),
                regulation_ref="SFDR – Regulation EU 2019/2088",
            ))

    return violations


def check_post_trade(
    trade: ExecutedTrade,
    portfolio: Portfolio,
    market_data: MarketData,
    ctx: dict,
) -> list[Violation]:
    violations: list[Violation] = []

    # ── EMEA-PT-001 MiFID II Art. 26 – Transaction Reporting (T+1) ───────────
    reporting_delay_hours = ctx.get("mifid_reporting_delay_hours", 0)
    if reporting_delay_hours > 24:
        violations.append(Violation(
            rule_id="EMEA-PT-001", rule_name="MiFID II Art. 26 – Late Transaction Report",
            jurisdiction=J, severity=Severity.BLOCK,
            message=(f"MiFID II transaction report for {trade.ticker} submitted {reporting_delay_hours}h after execution. "
                     f"Reports must be submitted no later than close of business T+1."),
            metric_value=float(reporting_delay_hours),
            threshold=24.0,
            regulation_ref="MiFID II Article 26 / MiFIR",
        ))

    # ── EMEA-PT-002 EMIR Trade Reporting – T+1 ───────────────────────────────
    if trade.asset_class == AssetClass.DERIVATIVE:
        emir_delay_hours = ctx.get("emir_reporting_delay_hours", 0)
        if emir_delay_hours > 24:
            violations.append(Violation(
                rule_id="EMEA-PT-002", rule_name="EMIR – Late Derivative Trade Report",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"EMIR derivative trade report for {trade.ticker} is {emir_delay_hours}h late. "
                         f"EMIR requires T+1 reporting to a Trade Repository."),
                metric_value=float(emir_delay_hours),
                threshold=24.0,
                regulation_ref="EMIR Article 9 (Regulation EU 648/2012)",
            ))

    # ── EMEA-PT-003 SFTR – Securities Financing Transaction Reporting ─────────
    if ctx.get("is_securities_financing_transaction"):
        sftr_delay_hours = ctx.get("sftr_reporting_delay_hours", 0)
        if sftr_delay_hours > 24:
            violations.append(Violation(
                rule_id="EMEA-PT-003", rule_name="SFTR – Late Securities Financing Report",
                jurisdiction=J, severity=Severity.BLOCK,
                message=(f"SFTR report for {trade.ticker} (repo/stock lending) is {sftr_delay_hours}h late. "
                         f"SFTR requires T+1 reporting."),
                metric_value=float(sftr_delay_hours),
                threshold=24.0,
                regulation_ref="SFTR Article 4 (Regulation EU 2015/2365)",
            ))

    return violations
