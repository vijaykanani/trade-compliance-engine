import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
DEFAULT_REGISTRY_PATH = APP_DIR / "rule_registry.json"
DEFAULT_AUDIT_PATH = APP_DIR / "rule_audit.json"

RULE_GROUPS = [
    "corporate",
    "usa",
    "emea",
    "public_markets",
    "private_markets",
    "digital_assets",
    "ai_governance",
]


def _default_registry() -> dict[str, dict[str, Any]]:
    return {
        "corporate": {
            "description": "Enterprise-wide restrictions, personal account dealing, and risk controls.",
            "rules": [
                {"id": "COR-001", "name": "Restricted Securities List", "severity": "BLOCK", "phase": "PRE", "regulation": "Internal Policy", "active": True, "notes": "Global restricted list"},
                {"id": "COR-002", "name": "Blackout / Closed Period", "severity": "BLOCK", "phase": "PRE", "regulation": "Internal Risk Policy", "active": True, "notes": "Earnings, M&A, and event blackouts"},
            ],
        },
        "usa": {
            "description": "US market rules covering SEC, FINRA, CFTC, and regulatory reporting.",
            "rules": [
                {"id": "USA-001", "name": "Reg SHO – Locate Requirement", "severity": "BLOCK", "phase": "PRE", "regulation": "Reg SHO Rule 203", "active": True, "notes": "Equity shortenings require locate"},
                {"id": "USA-002", "name": "SEC 13D/13G Disclosure Threshold", "severity": "WARNING", "phase": "PRE", "regulation": "Rule 13D/13G", "active": True, "notes": "Beneficial ownership monitoring"},
            ],
        },
        "emea": {
            "description": "EMEA rules for market abuse, short sales, and cross-border reporting.",
            "rules": [
                {"id": "EMEA-001", "name": "MAR Insider Trading", "severity": "BLOCK", "phase": "PRE", "regulation": "MAR Art. 8", "active": True, "notes": "Inside information checks"},
                {"id": "EMEA-002", "name": "MiFID II Best Execution", "severity": "WARNING", "phase": "PRE", "regulation": "MiFID II Art. 27", "active": True, "notes": "Execution quality review"},
            ],
        },
        "public_markets": {
            "description": "Public market compliance for equities, fixed income, and listed derivatives.",
            "rules": [
                {"id": "PUB-001", "name": "Public Equity Surveillance", "severity": "BLOCK", "phase": "PRE", "regulation": "Exchange and local market rules", "active": True, "notes": "Trade surveillance for public equities"},
                {"id": "PUB-002", "name": "Listed Derivatives Position Limit", "severity": "BLOCK", "phase": "PRE", "regulation": "Derivative exchange and CFTC rules", "active": True, "notes": "Commodity and derivative limits"},
            ],
        },
        "private_markets": {
            "description": "Private market checks for secondaries, direct lending, illiquid assets, and bespoke structures.",
            "rules": [
                {"id": "PRV-001", "name": "Private Deal Restriction", "severity": "BLOCK", "phase": "PRE", "regulation": "Private placement and investor restrictions", "active": True, "notes": "Investor eligibility and lock-up checks"},
                {"id": "PRV-002", "name": "Side Letter / Transfer Restriction", "severity": "WARNING", "phase": "PRE", "regulation": "Side letter and LP agreement requirements", "active": True, "notes": "Transfer restrictions, consents, rights of first refusal"},
            ],
        },
        "digital_assets": {
            "description": "Digital asset rules covering custody, wallet controls, sanctions, AML, and market manipulation.",
            "rules": [
                {"id": "DAS-001", "name": "Wallet Screening and Sanctions", "severity": "BLOCK", "phase": "PRE", "regulation": "OFAC, AML, FATF, travel rule", "active": True, "notes": "Blockchain wallet exposure screening"},
                {"id": "DAS-002", "name": "Stablecoin and Digital Asset Risk Review", "severity": "BLOCK", "phase": "PRE", "regulation": "MiCA, AMLD, local digital asset laws", "active": True, "notes": "Custody, token classification, liquidity checks"},
            ],
        },
        "ai_governance": {
            "description": "AI governance, model risk, monitoring, bias, privacy, and audit requirements.",
            "rules": [
                {"id": "AI-001", "name": "AI Model Risk Review", "severity": "BLOCK", "phase": "PRE", "regulation": "Model risk, AI governance, internal policy", "active": True, "notes": "Assess model use-case and risk tier"},
                {"id": "AI-002", "name": "Bias, Fairness, and Explainability Check", "severity": "WARNING", "phase": "PRE", "regulation": "AI governance and fairness standards", "active": True, "notes": "Requested for decision-support models"},
            ],
        },
    }


def load_rule_registry(path: str | Path | None = None) -> dict[str, Any]:
    file_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    if not file_path.exists():
        default = _default_registry()
        file_path.write_text(json.dumps(default, indent=2), encoding="utf-8")
        return default

    with file_path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError:
            data = _default_registry()
    if not isinstance(data, dict):
        data = _default_registry()

    for group in RULE_GROUPS:
        if group not in data:
            data[group] = {"description": f"{group.replace('_', ' ').title()} rules", "rules": []}
        if not isinstance(data[group], dict):
            data[group] = {"description": f"{group.replace('_', ' ').title()} rules", "rules": []}
        if "rules" not in data[group]:
            data[group]["rules"] = []
        if "description" not in data[group]:
            data[group]["description"] = f"{group.replace('_', ' ').title()} rules"

    return data


def save_rule_registry(data: dict[str, Any], path: str | Path | None = None) -> None:
    file_path = Path(path) if path is not None else DEFAULT_REGISTRY_PATH
    file_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_audit_log(path: str | Path | None = None) -> list[dict[str, Any]]:
    file_path = Path(path) if path is not None else DEFAULT_AUDIT_PATH
    if not file_path.exists():
        file_path.write_text("[]", encoding="utf-8")
        return []

    with file_path.open("r", encoding="utf-8") as fh:
        try:
            data = json.load(fh)
        except json.JSONDecodeError:
            return []
    return data if isinstance(data, list) else []


def save_audit_log(entries: list[dict[str, Any]], path: str | Path | None = None) -> None:
    file_path = Path(path) if path is not None else DEFAULT_AUDIT_PATH
    file_path.write_text(json.dumps(entries, indent=2), encoding="utf-8")


def append_audit_entry(action: str, jurisdiction: str, rule: dict[str, Any] | None, user: str = "local-admin", path: str | Path | None = None) -> dict[str, Any]:
    file_path = Path(path) if path is not None else DEFAULT_AUDIT_PATH
    entries = load_audit_log(file_path)
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "jurisdiction": jurisdiction,
        "user": user,
        "rule": rule,
    }
    entries.append(event)
    save_audit_log(entries, file_path)
    return event


def create_rule(
    jurisdiction: str,
    name: str,
    regulation: str,
    severity: str,
    phase: str,
    notes: str = "",
    registry: dict[str, Any] | None = None,
    registry_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    user: str = "local-admin",
) -> dict[str, Any]:
    data = registry if registry is not None else load_rule_registry(registry_path)
    jurisdiction_key = jurisdiction.lower()
    if jurisdiction_key not in RULE_GROUPS:
        raise ValueError(f"Unsupported jurisdiction: {jurisdiction}")

    bucket = data.setdefault(jurisdiction_key, {"description": f"{jurisdiction_key.replace('_', ' ').title()} rules", "rules": []})
    rule_id = f"{jurisdiction_key[:3].upper()}-{uuid.uuid4().hex[:8].upper()}"
    new_rule = {
        "id": rule_id,
        "name": name.strip(),
        "severity": severity.upper(),
        "phase": phase.upper(),
        "regulation": regulation.strip(),
        "active": True,
        "notes": notes,
    }
    bucket.setdefault("rules", []).append(new_rule)

    if registry is None:
        save_rule_registry(data, registry_path)
    append_audit_entry("create", jurisdiction_key, new_rule, user=user, path=audit_path)
    return new_rule


def delete_rule(
    jurisdiction: str,
    rule_id: str,
    registry: dict[str, Any] | None = None,
    registry_path: str | Path | None = None,
    audit_path: str | Path | None = None,
    user: str = "local-admin",
) -> bool:
    data = registry if registry is not None else load_rule_registry(registry_path)
    jurisdiction_key = jurisdiction.lower()
    if jurisdiction_key not in RULE_GROUPS:
        return False

    rules = data.setdefault(jurisdiction_key, {"description": f"{jurisdiction_key.replace('_', ' ').title()} rules", "rules": []}).setdefault("rules", [])
    for idx, rule in enumerate(rules):
        if rule.get("id") == rule_id:
            deleted_rule = dict(rule)
            del rules[idx]
            if registry is None:
                save_rule_registry(data, registry_path)
            append_audit_entry("delete", jurisdiction_key, deleted_rule, user=user, path=audit_path)
            return True
    return False


def update_rule(
    jurisdiction: str,
    rule_id: str,
    **changes: Any,
) -> dict[str, Any] | None:
    data = load_rule_registry(DEFAULT_REGISTRY_PATH)
    jurisdiction_key = jurisdiction.lower()
    rules = data.setdefault(jurisdiction_key, {"rules": []}).setdefault("rules", [])
    for rule in rules:
        if rule.get("id") == rule_id:
            for key, value in changes.items():
                if key in {"name", "severity", "phase", "regulation", "notes", "active"}:
                    rule[key] = value
            save_rule_registry(data, DEFAULT_REGISTRY_PATH)
            append_audit_entry("update", jurisdiction_key, dict(rule), path=DEFAULT_AUDIT_PATH)
            return rule
    return None
