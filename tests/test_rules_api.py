from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.routers import rules


def test_rule_mutations_require_a_configured_admin_key(monkeypatch):
    monkeypatch.setattr(rules, "get_settings", lambda: SimpleNamespace(rule_admin_api_key="test-admin-key"))

    with pytest.raises(HTTPException) as error:
        rules.require_rule_admin("")
    assert error.value.status_code == 403

    assert rules.require_rule_admin("test-admin-key") is None


def test_rule_mutations_fail_closed_without_a_configured_admin_key(monkeypatch):
    monkeypatch.setattr(rules, "get_settings", lambda: SimpleNamespace(rule_admin_api_key=""))

    with pytest.raises(HTTPException) as error:
        rules.require_rule_admin("any-key")
    assert error.value.status_code == 403