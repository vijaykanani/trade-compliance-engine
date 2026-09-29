import streamlit as st
import json
import os
import requests
from streamlit_app.demo_auth import require_demo_access

st.set_page_config(page_title="API Demo Console", page_icon="🔌", layout="wide")
require_demo_access()
st.title("🔌 External API Demo Console")
st.caption("Use this simulation page to validate the compliance API from an external app perspective.")

API_BASE = "http://localhost:8000"
API_HEADERS = {"X-Demo-Access-Secret": os.environ.get("DEMO_ACCESS_SECRET", "")}

with st.sidebar:
    st.subheader("API actions")
    action = st.selectbox("Action", ["Health Check", "Rule Export", "Order Import", "Trigger Compliance Run", "Violation Export"])

if action == "Health Check":
    resp = requests.get(f"{API_BASE}/health", headers=API_HEADERS, timeout=15)
    st.code(resp.text)

elif action == "Rule Export":
    resp = requests.get(f"{API_BASE}/rules/", headers=API_HEADERS, timeout=15)
    st.json(resp.json())

elif action == "Order Import":
    payload = {
        "order_id": "ORD-EXT-1001",
        "portfolio_id": "PORT-001",
        "security_id": "AAPL",
        "ticker": "AAPL",
        "asset_class": "EQUITY",
        "side": "BUY",
        "quantity": 5000,
        "price": 185.5,
        "currency": "USD",
        "trader_id": "T-100",
        "fund_jurisdiction": "USA",
        "strategy": "Long Equity",
    }
    resp = requests.post(f"{API_BASE}/compliance/pre-trade", json=payload, headers=API_HEADERS, timeout=15)
    st.code(resp.text)

elif action == "Trigger Compliance Run":
    payload = {
        "order_id": "ORD-EXT-1002",
        "portfolio_id": "PORT-001",
        "security_id": "BTCUSD",
        "ticker": "BTCUSD",
        "asset_class": "COMMODITY",
        "side": "BUY",
        "quantity": 2.5,
        "price": 60500,
        "currency": "USD",
        "trader_id": "T-200",
        "fund_jurisdiction": "USA",
        "strategy": "Digital Asset Pilot",
    }
    resp = requests.post(f"{API_BASE}/compliance/pre-trade", json=payload, headers=API_HEADERS, timeout=15)
    st.code(resp.text)

elif action == "Violation Export":
    resp = requests.get(f"{API_BASE}/compliance/breaches?limit=20", headers=API_HEADERS, timeout=15)
    st.json(resp.json())

st.divider()

st.subheader("Request builder")
method = st.selectbox("Method", ["GET", "POST", "DELETE"])
endpoint = st.text_input("Endpoint", value="/rules/")
body = st.text_area("JSON body", value="{}")

if st.button("Send request"):
    try:
        payload = json.loads(body) if body.strip() else None
        if method == "GET":
            response = requests.get(f"{API_BASE}{endpoint}", headers=API_HEADERS, timeout=15)
        elif method == "POST":
            response = requests.post(f"{API_BASE}{endpoint}", json=payload, headers=API_HEADERS, timeout=15)
        else:
            response = requests.delete(f"{API_BASE}{endpoint}", headers=API_HEADERS, timeout=15)
        st.code(f"Status: {response.status_code}\n{response.text}")
    except Exception as exc:
        st.error(str(exc))
