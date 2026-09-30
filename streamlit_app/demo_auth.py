import base64
import hashlib
import hmac
import json
import os
import time

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


def require_demo_access() -> None:
    import streamlit as st

    secret = os.environ.get("DEMO_ACCESS_SECRET")
    if not secret:
        return

    token = st.query_params.get("demo_access", "")
    if valid_demo_token(token, secret):
        st.session_state["_demo_access_token"] = token
        return

    session_token = st.session_state.get("_demo_access_token", "")
    if valid_demo_token(session_token, secret):
        return

    st.error("This Kens Control demo requires an approved, unexpired access link.")
    st.info("Request access from Kens Global to receive a personal demo link.")
    st.stop()