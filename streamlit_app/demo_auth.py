import base64
import hashlib
import hmac
import json
import os
import time
from urllib.parse import urlencode


PAGES = (
    ("Home", "/"),
    ("Pre-Trade Check", "/Pre_Trade_Check"),
    ("Post-Trade Check", "/Post_Trade_Check"),
    ("Breach Dashboard", "/Breach_Dashboard"),
    ("Rule Management", "/Rule_Management"),
    ("Domain Workflows", "/Domain_Workflows"),
)

def valid_demo_token(token: str, secret: str) -> bool:
    try:
        encoded, supplied_signature = token.split(".", 1)
        signature = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
        expected = base64.urlsafe_b64encode(signature).decode("ascii").rstrip("=")
        if not hmac.compare_digest(supplied_signature, expected):
            return False
        padded = encoded + "=" * (-len(encoded) % 4)
        payload = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))
        return payload.get("purpose") == "demo_access" and int(payload.get("exp", 0)) >= int(time.time())
    except (ValueError, TypeError, json.JSONDecodeError):
        return False


def demo_page_url(path: str) -> str:
    import streamlit as st

    secret = os.environ.get("DEMO_ACCESS_SECRET", "")
    token = st.query_params.get("demo_access", "")
    if not valid_demo_token(token, secret):
        token = st.session_state.get("_demo_access_token", "")
    if not secret or not valid_demo_token(token, secret):
        return path

    separator = "&" if "?" in path else "?"
    return f"{path}{separator}{urlencode({'demo_access': token})}"


def render_demo_page_link(path: str, label: str) -> None:
    import streamlit as st

    st.markdown(f"[{label}]({demo_page_url(path)})")


def render_demo_navigation() -> None:
    import streamlit as st

    st.sidebar.markdown("**Navigation**")
    for label, path in PAGES:
        render_demo_page_link(path, label)


def require_demo_access() -> None:
    import streamlit as st

    secret = os.environ.get("DEMO_ACCESS_SECRET")
    if not secret:
        render_demo_navigation()
        return

    token = st.query_params.get("demo_access", "")
    if valid_demo_token(token, secret):
        st.session_state["_demo_access_token"] = token
        render_demo_navigation()
        return

    session_token = st.session_state.get("_demo_access_token", "")
    if valid_demo_token(session_token, secret):
        render_demo_navigation()
        return

    st.error("This Kens Control demo requires an approved, unexpired access link.")
    st.info("Request access from Kens Global to receive a personal demo link.")
    st.stop()