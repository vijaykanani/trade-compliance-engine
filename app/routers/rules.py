import os
import json
from fastapi import APIRouter

router = APIRouter(prefix="/rules", tags=["Rules"])

RULES_DIR = os.path.join(os.path.dirname(__file__), "../../decision_rules_config")


@router.get("/", summary="List available rule sets")
async def list_rule_sets():
    return {
        "corporate": {
            "description": "Firm-wide corporate restrictions (restricted list, blackout, mandate, etc.)",
            "rules": _corporate_rule_index(),
        },
        "usa": {
            "description": "US regulatory rules (SEC, FINRA, CFTC, Volcker, Reg T, etc.)",
            "rules": _usa_rule_index(),
        },
        "emea": {
            "description": "EMEA regulatory rules (MiFID II, MAR, EMIR, UCITS, SFDR, etc.)",
            "rules": _emea_rule_index(),
        },
    }


@router.get("/corporate", summary="Corporate restriction rules")
async def corporate_rules():
    return {"rules": _corporate_rule_index()}


@router.get("/usa", summary="USA regulatory rules")
async def usa_rules():
    return {"rules": _usa_rule_index()}


@router.get("/emea", summary="EMEA regulatory rules")
async def emea_rules():
    return {"rules": _emea_rule_index()}


@router.get("/decision-rules-config/{name}", summary="Get DecisionRules.io JSON config")
async def get_dr_config(name: str):
    allowed = {"pre_trade_corporate", "pre_trade_usa", "pre_trade_emea",
               "post_trade_corporate", "post_trade_usa", "post_trade_emea"}
    if name not in allowed:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Config not found")

    path = os.path.join(RULES_DIR, f"{name}.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"error": "Config file not yet generated — run /rules/reload"}


def _corporate_rule_index():
    return [
        {"id": "CORP-001", "name": "Restricted Securities List",           "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-002", "name": "Watch List – Heightened Monitoring",   "severity": "WARNING", "phase": "PRE"},
        {"id": "CORP-003", "name": "Blackout Period",                      "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-004", "name": "Employee Personal Account Dealing",    "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-005", "name": "Information Barrier / Chinese Wall",   "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-006", "name": "Mandate Breach – Bond-Only Fund",      "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-007", "name": "Mandate Breach – Equity-Only Fund",    "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-008", "name": "Single Issuer Position Limit",         "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-009", "name": "Sector Concentration Limit",           "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-010", "name": "Short Sell Without Locate",            "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-011", "name": "Unapproved Counterparty / Broker",    "severity": "BLOCK",   "phase": "PRE"},
        {"id": "CORP-012", "name": "Daily Turnover Limit Warning",         "severity": "WARNING", "phase": "PRE"},
        {"id": "CORP-PT-001", "name": "Daily P&L Hard Stop",              "severity": "BLOCK",   "phase": "POST"},
        {"id": "CORP-PT-002", "name": "Wash Trade Detection",             "severity": "WARNING", "phase": "POST"},
        {"id": "CORP-PT-003", "name": "Post-Trade Position Limit Breach", "severity": "BLOCK",   "phase": "POST"},
    ]


def _usa_rule_index():
    return [
        {"id": "USA-001", "name": "Reg SHO – Short Sale Locate",              "regulation": "Reg SHO Rule 203",          "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-002", "name": "Reg SHO – Threshold Security",             "regulation": "Reg SHO Rule 203(b)(3)",    "severity": "WARNING", "phase": "PRE"},
        {"id": "USA-003", "name": "Regulation T – Initial Margin",            "regulation": "Regulation T",              "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-004", "name": "SEC 13D/G – 5% Beneficial Ownership",      "regulation": "Rule 13D/13G",              "severity": "WARNING", "phase": "PRE"},
        {"id": "USA-005", "name": "SEC Rule 16 – 10% Insider Threshold",      "regulation": "Exchange Act Section 16",   "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-006", "name": "ICA – 5% Diversification Test",            "regulation": "ICA 1940 Section 5(b)(1)", "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-007", "name": "ICA – 25% Industry Concentration",         "regulation": "ICA 1940 Section 5(b)(1)", "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-008", "name": "Volcker Rule – Proprietary Trading",        "regulation": "BHC Act Section 619",      "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-009", "name": "SEC Rule 144 – Restricted Securities",     "regulation": "SEC Rule 144",             "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-010", "name": "FINRA PDT – Pattern Day Trader",           "regulation": "FINRA Rule 4210",           "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-011", "name": "CFTC Position Limits – Derivatives",       "regulation": "CFTC Part 150",            "severity": "BLOCK",   "phase": "PRE"},
        {"id": "USA-012", "name": "Regulation NMS – Best Execution",          "regulation": "Reg NMS Rule 611",         "severity": "WARNING", "phase": "PRE"},
        {"id": "USA-PT-001", "name": "FINRA TRACE – 15-min Bond Reporting",  "regulation": "FINRA Rule 6730",           "severity": "BLOCK",   "phase": "POST"},
        {"id": "USA-PT-002", "name": "SEC 13F – Institutional Reporting",     "regulation": "Exchange Act Section 13(f)","severity": "WARNING", "phase": "POST"},
        {"id": "USA-PT-003", "name": "Reg SHO – Failure to Deliver",         "regulation": "Reg SHO Rule 204",          "severity": "BLOCK",   "phase": "POST"},
    ]


def _emea_rule_index():
    return [
        {"id": "EMEA-001", "name": "MAR – Insider Trading",                       "regulation": "MAR Art. 8",           "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-002", "name": "MAR – Market Manipulation",                   "regulation": "MAR Art. 12",          "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-003", "name": "EU SSR – Net Short 0.1% Notification",        "regulation": "SSR Art. 5",           "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-004", "name": "EU SSR – Net Short 0.5% Public Disclosure",   "regulation": "SSR Art. 6",           "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-005", "name": "EU SSR – Uncovered Short Sale Prohibited",    "regulation": "SSR Art. 12",          "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-006", "name": "MiFID II Art. 57 – ESMA Position Limits",     "regulation": "MiFID II Art. 57",     "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-007", "name": "MiFID II Art. 27 – Best Execution",           "regulation": "MiFID II Art. 27",     "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-008", "name": "UCITS – 5% Single Issuer Limit",              "regulation": "UCITS Art. 52",        "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-009", "name": "UCITS – 40% Bucket Rule",                     "regulation": "UCITS Art. 52(2)",     "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-010", "name": "AIFMD – Leverage Limit",                      "regulation": "AIFMD Art. 15",        "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-011", "name": "EMIR – Mandatory Central Clearing",           "regulation": "EMIR Art. 4",          "severity": "BLOCK",   "phase": "PRE"},
        {"id": "EMEA-012", "name": "EMIR – Bilateral Margin Requirements",        "regulation": "EMIR RTS",             "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-013", "name": "UK FCA DTR 5 – Major Shareholding",           "regulation": "FCA DTR 5",            "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-014", "name": "EU Transparency – 5% Shareholding",           "regulation": "Transparency Dir.",    "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-015", "name": "MAR – Suspicious Transaction Report (STR)",   "regulation": "MAR Art. 16",          "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-016", "name": "SFDR – ESG Score Below Threshold",            "regulation": "SFDR 2019/2088",       "severity": "WARNING", "phase": "PRE"},
        {"id": "EMEA-PT-001", "name": "MiFID II Art. 26 – Transaction Reporting", "regulation": "MiFID II Art. 26",     "severity": "BLOCK",   "phase": "POST"},
        {"id": "EMEA-PT-002", "name": "EMIR – Derivative Trade Reporting",        "regulation": "EMIR Art. 9",          "severity": "BLOCK",   "phase": "POST"},
        {"id": "EMEA-PT-003", "name": "SFTR – SFT Reporting",                     "regulation": "SFTR Art. 4",          "severity": "BLOCK",   "phase": "POST"},
    ]
