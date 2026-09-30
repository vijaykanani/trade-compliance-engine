import base64
import hashlib
import hmac
import json
import sys
import time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from streamlit_app.demo_auth import render_demo_navigation, require_demo_access


def make_token(secret: str, expires_at: int) -> str:
    encoded = base64.urlsafe_b64encode(
        json.dumps({"purpose": "demo_access", "exp": expires_at}).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    supplied_signature = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
    return f"{encoded}.{supplied_signature}"


def test_valid_access_survives_page_navigation_without_query_parameter(monkeypatch):
    secret = "test-secret"
    token = make_token(secret, int(time.time()) + 60)
    fake_streamlit = SimpleNamespace(
        query_params={"demo_access": token},
        session_state={},
        sidebar=SimpleNamespace(markdown=Mock()),
        markdown=Mock(),
        error=Mock(),
        info=Mock(),
        stop=Mock(side_effect=RuntimeError("stopped")),
    )
    monkeypatch.setenv("DEMO_ACCESS_SECRET", secret)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    require_demo_access()
    fake_streamlit.query_params = {}
    require_demo_access()

    assert fake_streamlit.session_state["_demo_access_token"] == token
    fake_streamlit.stop.assert_not_called()


def test_navigation_links_carry_valid_access_token(monkeypatch):
    secret = "test-secret"
    token = make_token(secret, int(time.time()) + 60)
    fake_streamlit = SimpleNamespace(
        query_params={"demo_access": token},
        session_state={},
        sidebar=SimpleNamespace(markdown=Mock()),
        markdown=Mock(),
    )
    monkeypatch.setenv("DEMO_ACCESS_SECRET", secret)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    render_demo_navigation()

    rendered_links = [call.args[0] for call in fake_streamlit.markdown.call_args_list]
    assert f"[Pre-Trade Check](/Pre_Trade_Check?demo_access={token})" in rendered_links
    assert f"[Domain Workflows](/Domain_Workflows?demo_access={token})" in rendered_links


def test_expired_session_token_is_rejected(monkeypatch):
    secret = "test-secret"
    fake_streamlit = SimpleNamespace(
        query_params={},
        session_state={"_demo_access_token": make_token(secret, int(time.time()) - 1)},
        sidebar=SimpleNamespace(markdown=Mock()),
        error=Mock(),
        info=Mock(),
        stop=Mock(side_effect=RuntimeError("stopped")),
    )
    monkeypatch.setenv("DEMO_ACCESS_SECRET", secret)
    monkeypatch.setitem(sys.modules, "streamlit", fake_streamlit)

    with pytest.raises(RuntimeError, match="stopped"):
        require_demo_access()

    fake_streamlit.error.assert_called_once()