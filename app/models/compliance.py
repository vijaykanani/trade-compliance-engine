from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import Optional


class Severity(str, Enum):
    BLOCK = "BLOCK"
    WARNING = "WARNING"
    INFO = "INFO"


class CheckStatus(str, Enum):
    APPROVED = "APPROVED"
    BLOCKED = "BLOCKED"
    WARNING = "WARNING"
    PENDING_REVIEW = "PENDING_REVIEW"


class RuleJurisdiction(str, Enum):
    CORPORATE = "CORPORATE"
    USA = "USA"
    EMEA = "EMEA"
    GLOBAL = "GLOBAL"


class Violation(BaseModel):
    rule_id: str
    rule_name: str
    jurisdiction: RuleJurisdiction
    severity: Severity
    message: str
    metric_value: Optional[float] = None
    threshold: Optional[float] = None
    regulation_ref: Optional[str] = None           # e.g. "SEC Rule 15c3-5", "MiFID II Art.27"


class ComplianceResult(BaseModel):
    order_id: str
    portfolio_id: str
    passed: bool
    status: CheckStatus
    violations: list[Violation] = []
    warnings: list[Violation] = []
    checked_rules: list[str] = []
    rule_source: str = "LOCAL"                     # LOCAL | DECISION_RULES
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    reviewed_by: Optional[str] = None
    notes: Optional[str] = None


class BreachRecord(BaseModel):
    breach_id: str
    order_id: str
    portfolio_id: str
    trader_id: str
    ticker: str
    breach_type: str
    jurisdiction: str
    severity: str
    message: str
    regulation_ref: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
