from streamlit_app.domain_workflows import evaluate_assessment, load_assessments, save_assessment


def test_private_secondary_transfer_requires_transfer_clearance():
    facts = {
        "activity": "Secondary transfer",
        "kyc_complete": True,
        "investor_eligible": True,
        "documents_reviewed": True,
        "conflicts_cleared": True,
        "concentration_reviewed": True,
        "transfer_approved": False,
    }

    result = evaluate_assessment("private_markets", facts)

    assert result["status"] == "BLOCKED"
    assert "PRV-TRANSFER-01" in {finding["rule_id"] for finding in result["findings"]}


def test_digital_travel_rule_is_only_checked_when_applicable():
    facts = {
        "travel_rule_required": "not applicable",
        "sanctions_clear": True,
        "wallet_screened": True,
        "jurisdiction_supported": True,
        "custody_approved": True,
        "travel_rule_complete": False,
        "token_reviewed": True,
        "protocol_reviewed": True,
    }

    result = evaluate_assessment("digital_assets", facts)

    assert result["status"] == "APPROVED"
    assert "DIG-TR-01" not in result["checked_rules"]


def test_ai_provider_review_is_conditional_and_assessment_is_persisted(tmp_path):
    facts = {
        "third_party": "no",
        "risk_classified": True,
        "use_case_approved": True,
        "data_cleared": True,
        "model_validated": True,
        "fairness_tested": True,
        "human_oversight": True,
        "monitoring_ready": True,
        "vendor_reviewed": False,
    }
    result = evaluate_assessment("ai_governance", facts)
    assert result["status"] == "APPROVED"
    assert "AIG-VENDOR-01" not in result["checked_rules"]

    history_path = tmp_path / "assessments.json"
    record = save_assessment("ai_governance", "MODEL-1", facts, "reviewer-1", path=history_path)

    assert record["status"] == "APPROVED"
    assert load_assessments(history_path) == [record]