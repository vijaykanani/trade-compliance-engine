from streamlit_app.rule_store import create_rule, delete_rule, load_rule_registry, load_audit_log


def test_create_and_delete_rule_updates_audit(tmp_path):
    registry_path = tmp_path / "rule_registry.json"
    audit_path = tmp_path / "rule_audit.json"

    registry = {
        "corporate": {"rules": []},
        "usa": {"rules": []},
        "emea": {"rules": []},
    }

    created = create_rule(
        jurisdiction="corporate",
        name="Test Internal Rule",
        regulation="Internal Policy",
        severity="BLOCK",
        phase="PRE",
        notes="Temp test rule",
        registry=registry,
        registry_path=registry_path,
        audit_path=audit_path,
    )

    assert created["name"] == "Test Internal Rule"
    assert created["active"] is True
    assert len(load_audit_log(audit_path)) >= 1

    removed = delete_rule(
        jurisdiction="corporate",
        rule_id=created["id"],
        registry=registry,
        registry_path=registry_path,
        audit_path=audit_path,
    )

    assert removed is True
    stored = load_rule_registry(registry_path)
    assert all(rule["id"] != created["id"] for rule in stored["corporate"]["rules"])
