import json
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.models.trade import TradeOrder, ExecutedTrade
from app.models.compliance import ComplianceResult
from app.engines.pre_trade import run_pre_trade_check
from app.engines.post_trade import run_post_trade_check
from app.services.portfolio_service import get_portfolio, get_market_data
from app.db.database import get_db, log_compliance_result, BreachLog

router = APIRouter(prefix="/compliance", tags=["Compliance"])


@router.post("/pre-trade", response_model=ComplianceResult, summary="Pre-Trade Compliance Check")
async def pre_trade_check(
    order: TradeOrder,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs all applicable compliance rules before an order is placed.
    Returns APPROVED or BLOCKED with full violation details.
    """
    portfolio = await get_portfolio(order.portfolio_id)
    market_data = await get_market_data(order.security_id)

    result = await run_pre_trade_check(order, portfolio, market_data)

    await log_compliance_result(db, result, "PRE_TRADE", order.trader_id, order.ticker)
    return result


@router.post("/post-trade", response_model=ComplianceResult, summary="Post-Trade Compliance Check")
async def post_trade_check(
    trade: ExecutedTrade,
    db: AsyncSession = Depends(get_db),
):
    """
    Runs compliance checks after a trade has been executed.
    Detects breaches, reporting failures, wash trades, P&L stops.
    """
    portfolio = await get_portfolio(trade.portfolio_id)
    market_data = await get_market_data(trade.security_id)

    result = await run_post_trade_check(trade, portfolio, market_data)

    await log_compliance_result(db, result, "POST_TRADE", trade.trader_id, trade.ticker)
    return result


@router.get("/breaches", summary="Get Breach History")
async def get_breaches(
    portfolio_id: str | None = None,
    check_type: str | None = None,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """Return recent compliance check history with violations."""
    query = select(BreachLog).order_by(desc(BreachLog.timestamp)).limit(limit)
    if portfolio_id:
        query = query.where(BreachLog.portfolio_id == portfolio_id)
    if check_type:
        query = query.where(BreachLog.check_type == check_type)

    result = await db.execute(query)
    rows = result.scalars().all()

    return [
        {
            "id": r.id,
            "order_id": r.order_id,
            "portfolio_id": r.portfolio_id,
            "trader_id": r.trader_id,
            "ticker": r.ticker,
            "check_type": r.check_type,
            "rule_source": r.rule_source,
            "passed": r.passed,
            "status": r.status,
            "violations": json.loads(r.violations_json or "[]"),
            "warnings": json.loads(r.warnings_json or "[]"),
            "timestamp": r.timestamp.isoformat(),
            "resolved": r.resolved,
        }
        for r in rows
    ]


class ResolveRequest(BaseModel):
    resolved_by: str
    notes: str | None = None


@router.post("/breaches/{breach_id}/resolve", summary="Mark Breach as Resolved")
async def resolve_breach(
    breach_id: str,
    body: ResolveRequest,
    db: AsyncSession = Depends(get_db),
):
    from datetime import datetime
    result = await db.execute(select(BreachLog).where(BreachLog.id == breach_id))
    record = result.scalar_one_or_none()
    if not record:
        raise HTTPException(status_code=404, detail="Breach record not found")

    record.resolved = True
    record.resolved_by = body.resolved_by
    record.resolved_at = datetime.utcnow()
    record.notes = body.notes
    await db.commit()
    return {"status": "resolved", "breach_id": breach_id}


@router.get("/stats", summary="Compliance Statistics")
async def compliance_stats(db: AsyncSession = Depends(get_db)):
    """Summary statistics for the compliance dashboard."""
    all_result = await db.execute(select(BreachLog))
    rows = all_result.scalars().all()

    total = len(rows)
    blocked = sum(1 for r in rows if not r.passed)
    approved = sum(1 for r in rows if r.passed)
    unresolved = sum(1 for r in rows if not r.passed and not r.resolved)
    pre_trade = sum(1 for r in rows if r.check_type == "PRE_TRADE")
    post_trade = sum(1 for r in rows if r.check_type == "POST_TRADE")

    return {
        "total_checks": total,
        "approved": approved,
        "blocked": blocked,
        "unresolved_breaches": unresolved,
        "pre_trade_checks": pre_trade,
        "post_trade_checks": post_trade,
        "block_rate_pct": round(blocked / total * 100, 2) if total else 0,
    }
