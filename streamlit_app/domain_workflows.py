import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

APP_DIR = Path(__file__).resolve().parent
ASSESSMENT_PATH = APP_DIR / "domain_assessments.json"

DOMAIN_RULES: dict[str, list[dict[str, str]]] = {
    "private_markets": [
        {"id": "PRV-KYC-01", "name": "Investor and counterparty due diligence", "field": "kyc_complete", "severity": "BLOCK", "reference": "AML/KYC requirements; FATF recommendations"},
        {"id": "PRV-ELIG-01", "name": "Investor eligibility and offering restrictions", "field": "investor_eligible", "severity": "BLOCK", "reference": "Securities offering exemptions; investor qualification rules"},
        {"id": "PRV-DOC-01", "name": "Governing documents and side-letter review", "field": "documents_reviewed", "severity": "REVIEW", "reference": "LPA, subscription documents, side letters, and mandate terms"},
        {"id": "PRV-CONFLICT-01", "name": "Conflicts of interest assessment", "field": "conflicts_cleared", "severity": "BLOCK", "reference": "Adviser fiduciary duties; conflicts policies"},
        {"id": "PRV-CONC-01", "name": "Portfolio concentration review", "field": "concentration_reviewed", "severity": "REVIEW", "reference": "Fund mandate and concentration limits"},
        {"id": "PRV-TRANSFER-01", "name": "Transfer consent and rights review", "field": "transfer_approved", "severity": "BLOCK", "reference": "LPA, transfer restrictions, ROFR/ROFO, and consent provisions", "when_field": "activity", "when_value": "Secondary transfer"},
        {"id": "PRV-VAL-01", "name": "Valuation support and approval", "field": "valuation_supported", "severity": "REVIEW", "reference": "Fund valuation policy; applicable fair-value standards", "when_field": "activity", "when_value": "Valuation event"},
    ],
    "digital_assets": [
        {"id": "DIG-SAN-01", "name": "Wallet and counterparty sanctions screening", "field": "sanctions_clear", "severity": "BLOCK", "reference": "OFAC sanctions programs; applicable local sanctions rules"},
        {"id": "DIG-KYT-01", "name": "Wallet exposure and transaction monitoring", "field": "wallet_screened", "severity": "BLOCK", "reference": "Applicable AML/CFT and risk-based monitoring requirements"},
        {"id": "DIG-LIC-01", "name": "Jurisdiction and service-provider authorization", "field": "jurisdiction_supported", "severity": "BLOCK", "reference": "MiCA (EU); applicable VASP/CASP licensing and local rules"},
        {"id": "DIG-CUST-01", "name": "Custody and asset-control review", "field": "custody_approved", "severity": "REVIEW", "reference": "Custody safeguarding, segregation, and key-management controls"},
        {"id": "DIG-TR-01", "name": "Travel Rule information exchange", "field": "travel_rule_complete", "severity": "BLOCK", "reference": "FATF Recommendation 16 and implementing local rules", "when_field": "travel_rule_required", "when_value": "yes"},
        {"id": "DIG-TOKEN-01", "name": "Token classification and product review", "field": "token_reviewed", "severity": "REVIEW", "reference": "MiCA; securities, commodities, and payments classification rules"},
        {"id": "DIG-SC-01", "name": "Smart-contract and protocol risk assessment", "field": "protocol_reviewed", "severity": "REVIEW", "reference": "Internal technology, cyber, and operational-risk controls", "when_field": "activity", "when_value": "DeFi / protocol interaction"},
    ],
    "ai_governance": [
        {"id": "AIG-RISK-01", "name": "AI system risk classification and inventory", "field": "risk_classified", "severity": "BLOCK", "reference": "EU AI Act (where applicable); internal AI risk taxonomy"},
        {"id": "AIG-LAW-01", "name": "Prohibited-use and legal-basis review", "field": "use_case_approved", "severity": "BLOCK", "reference": "EU AI Act prohibited practices (where applicable); local law"},
        {"id": "AIG-DATA-01", "name": "Data provenance, rights, and privacy review", "field": "data_cleared", "severity": "BLOCK", "reference": "GDPR and applicable privacy, data protection, and IP rules"},
        {"id": "AIG-VALID-01", "name": "Independent model validation and testing", "field": "model_validated", "severity": "REVIEW", "reference": "Model risk management policy; NIST AI RMF"},
        {"id": "AIG-FAIR-01", "name": "Bias, performance, and explainability testing", "field": "fairness_tested", "severity": "REVIEW", "reference": "EU AI Act (where applicable); applicable anti-discrimination rules"},
        {"id": "AIG-HUMAN-01", "name": "Human oversight and escalation design", "field": "human_oversight", "severity": "BLOCK", "reference": "EU AI Act high-risk obligations (where applicable); internal controls"},
        {"id": "AIG-MON-01", "name": "Post-deployment monitoring and incident response", "field": "monitoring_ready", "severity": "REVIEW", "reference": "EU AI Act (where applicable); NIST AI RMF"},
        {"id": "AIG-VENDOR-01", "name": "Third-party model and supplier due diligence", "field": "vendor_reviewed", "severity": "REVIEW", "reference": "Third-party risk management and contractual controls", "when_field": "third_party", "when_value": "yes"},
    ],
}


def evaluate_assessment(domain: str, facts: dict[str, Any]) -> dict[str, Any]:
    if domain not in DOMAIN_RULES:
        raise ValueError(f"Unsupported assessment domain: {domain}")

    findings = []
    checked_rules = []
    for rule in DOMAIN_RULES[domain]:
        if "when_field" in rule and str(facts.get(rule["when_field"], "")).lower() != rule["when_value"].lower():
            continue
        checked_rules.append(rule["id"])
        if facts.get(rule["field"]) is not True:
            findings.append({
                "rule_id": rule["id"],
                "rule_name": rule["name"],
                "severity": rule["severity"],
                "reference": rule["reference"],
                "message": f"Evidence or approval is missing for: {rule['name']}.",
            })

    if any(finding["severity"] == "BLOCK" for finding in findings):
        status = "BLOCKED"
    elif findings:
        status = "PENDING_REVIEW"
    else:
        status = "APPROVED"

    return {"status": status, "findings": findings, "checked_rules": checked_rules}


def load_assessments(path: str | Path | None = None) -> list[dict[str, Any]]:
    file_path = Path(path) if path is not None else ASSESSMENT_PATH
    if not file_path.exists():
        return []
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    return data if isinstance(data, list) else []


def save_assessment(domain: str, subject: str, facts: dict[str, Any], reviewer: str, notes: str = "", path: str | Path | None = None) -> dict[str, Any]:
    result = evaluate_assessment(domain, facts)
    record = {
        "assessment_id": f"ASM-{uuid.uuid4().hex[:10].upper()}",
        "domain": domain,
        "subject": subject.strip(),
        "status": result["status"],
        "facts": facts,
        "findings": result["findings"],
        "checked_rules": result["checked_rules"],
        "reviewer": reviewer.strip(),
        "notes": notes,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    file_path = Path(path) if path is not None else ASSESSMENT_PATH
    assessments = load_assessments(file_path)
    assessments.append(record)
    file_path.write_text(json.dumps(assessments, indent=2), encoding="utf-8")
    return record