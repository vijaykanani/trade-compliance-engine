import uuid
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, String, Boolean, Float, DateTime, Text
from app.config import get_settings

settings = get_settings()
engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()


class BreachLog(Base):
    __tablename__ = "breach_log"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    order_id = Column(String, index=True)
    portfolio_id = Column(String, index=True)
    trader_id = Column(String)
    ticker = Column(String)
    check_type = Column(String)          # PRE_TRADE | POST_TRADE
    rule_source = Column(String)         # LOCAL | DECISION_RULES
    passed = Column(Boolean)
    status = Column(String)
    violations_json = Column(Text)       # JSON list of violations
    warnings_json = Column(Text)
    checked_rules_json = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    resolved = Column(Boolean, default=False)
    resolved_by = Column(String, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


async def log_compliance_result(session: AsyncSession, result, check_type: str, trader_id: str, ticker: str):
    from sqlalchemy import text
    record = BreachLog(
        order_id=result.order_id,
        portfolio_id=result.portfolio_id,
        trader_id=trader_id,
        ticker=ticker,
        check_type=check_type,
        rule_source=result.rule_source,
        passed=result.passed,
        status=result.status.value,
        violations_json=json.dumps([v.model_dump() for v in result.violations]),
        warnings_json=json.dumps([w.model_dump() for w in result.warnings]),
        checked_rules_json=json.dumps(result.checked_rules),
    )
    session.add(record)
    await session.commit()
    return record
