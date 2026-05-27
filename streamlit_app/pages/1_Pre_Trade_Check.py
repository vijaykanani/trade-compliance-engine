import streamlit as st
import json
from datetime import datetime
from streamlit_app.utils.api_client import post_sync

st.set_page_config(page_title="Pre-Trade Check", page_icon="🔍", layout="wide")
st.title("🔍 Pre-Trade Compliance Check")
st.caption("Validate an order before it is placed. Checks Corporate, USA, and EMEA rules.")

# ── Order Entry Form ─────────────────────────────────────────────────────────
with st.form("pre_trade_form"):
    st.subheader("Order Details")

    col1, col2, col3 = st.columns(3)
    with col1:
        order_id    = st.text_input("Order ID", value=f"ORD-{datetime.utcnow().strftime('%H%M%S')}")
        portfolio_id = st.selectbox("Portfolio", ["FUND-USA-01", "FUND-EMEA-01", "FUND-BOND-01", "CUSTOM"])
        if portfolio_id == "CUSTOM":
            portfolio_id = st.text_input("Custom Portfolio ID")
        ticker      = st.text_input("Ticker", value="AAPL")
        security_id = st.text_input("Security ID", value="AAPL")

    with col2:
        asset_class = st.selectbox("Asset Class", ["EQUITY", "BOND", "DERIVATIVE", "FX", "COMMODITY", "ETF"])
        side        = st.selectbox("Side", ["BUY", "SELL", "SHORT", "COVER"])
        order_type  = st.selectbox("Order Type", ["MARKET", "LIMIT", "STOP"])
        currency    = st.selectbox("Currency", ["USD", "EUR", "GBP", "CHF", "JPY"])

    with col3:
        quantity    = st.number_input("Quantity", min_value=1, value=10000, step=100)
        price       = st.number_input("Price", min_value=0.01, value=185.50, step=0.01, format="%.2f")
        trader_id   = st.text_input("Trader ID", value="T001")
        jurisdiction = st.selectbox("Fund Jurisdiction", ["USA", "EMEA", "APAC"])

    st.divider()
    st.subheader("Additional Context (Optional)")
    col4, col5 = st.columns(2)
    with col4:
        is_margin_account   = st.checkbox("Margin Account")
        is_registered_fund  = st.checkbox("Registered Fund (ICA)")
        is_ucits_fund       = st.checkbox("UCITS Fund")
        is_aifmd_fund       = st.checkbox("AIFMD Fund")
        is_banking_entity   = st.checkbox("Banking Entity (Volcker)")

    with col5:
        has_inside_info     = st.checkbox("Has Inside Information (MAR)")
        is_prop_trade       = st.checkbox("Proprietary Trade")
        is_sfdr_art8_9      = st.checkbox("SFDR Article 8/9 Fund")
        is_emir_clearing    = st.checkbox("EMIR Clearing Obligated")
        is_144_restricted   = st.checkbox("Rule 144 Restricted Security")

    submitted = st.form_submit_button("Run Pre-Trade Check", type="primary", use_container_width=True)

# ── Result ───────────────────────────────────────────────────────────────────
if submitted:
    payload = {
        "order_id": order_id,
        "portfolio_id": portfolio_id,
        "security_id": security_id,
        "ticker": ticker,
        "asset_class": asset_class,
        "side": side,
        "order_type": order_type,
        "quantity": float(quantity),
        "price": float(price),
        "currency": currency,
        "trader_id": trader_id,
        "fund_jurisdiction": jurisdiction,
    }

    extra_ctx = {
        "is_margin_account":          is_margin_account,
        "is_registered_fund":         is_registered_fund,
        "is_ucits_fund":              is_ucits_fund,
        "is_aifmd_fund":              is_aifmd_fund,
        "is_banking_entity":          is_banking_entity,
        "is_prop_trade":              is_prop_trade,
        "has_inside_information":     has_inside_info,
        "is_sfdr_article8_or_9":      is_sfdr_art8_9,
        "is_emir_clearing_obligated": is_emir_clearing,
        "is_restricted_security_rule144": is_144_restricted,
    }

    with st.spinner("Running compliance checks..."):
        try:
            # Pass extra_ctx as query params via a combined payload workaround:
            # The API accepts extra fields in the order body and routes them to ctx
            full_payload = {**payload, **extra_ctx}
            result = post_sync("/compliance/pre-trade", payload)
            st.session_state["last_pre_trade"] = result
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    # ── Status Banner ────────────────────────────────────────────────────────
    status = result.get("status", "UNKNOWN")
    passed = result.get("passed", False)

    if passed:
        st.success(f"✅ **{status}** — Order cleared all compliance checks")
    else:
        st.error(f"🚫 **{status}** — Order blocked. See violations below.")

    # ── Metrics Row ──────────────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", status)
    m2.metric("Violations (BLOCK)", len(result.get("violations", [])))
    m3.metric("Warnings", len(result.get("warnings", [])))
    m4.metric("Rules Checked", len(result.get("checked_rules", [])))

    st.caption(f"Rule source: **{result.get('rule_source', 'LOCAL')}**  |  Timestamp: {result.get('timestamp', '')}")

    # ── Violations ───────────────────────────────────────────────────────────
    violations = result.get("violations", [])
    if violations:
        st.subheader("🚫 Violations (BLOCK)")
        for v in violations:
            with st.expander(f"[{v['rule_id']}] {v['rule_name']}", expanded=True):
                st.error(v["message"])
                cols = st.columns(3)
                cols[0].write(f"**Jurisdiction:** {v.get('jurisdiction', '-')}")
                cols[1].write(f"**Metric:** {v.get('metric_value', '-')}")
                cols[2].write(f"**Threshold:** {v.get('threshold', '-')}")
                if v.get("regulation_ref"):
                    st.caption(f"Regulation: {v['regulation_ref']}")

    # ── Warnings ─────────────────────────────────────────────────────────────
    warnings = result.get("warnings", [])
    if warnings:
        st.subheader("⚠️ Warnings")
        for w in warnings:
            with st.expander(f"[{w['rule_id']}] {w['rule_name']}"):
                st.warning(w["message"])
                if w.get("regulation_ref"):
                    st.caption(f"Regulation: {w['regulation_ref']}")

    if passed and not warnings:
        st.info("No issues found. Order is compliant.")

    # ── Raw JSON ─────────────────────────────────────────────────────────────
    with st.expander("Raw JSON Response"):
        st.json(result)
