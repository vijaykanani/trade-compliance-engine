import streamlit as st
from datetime import datetime
from streamlit_app.utils.api_client import post_sync

st.set_page_config(page_title="Post-Trade Check", page_icon="📋", layout="wide")
st.title("📋 Post-Trade Compliance Check")
st.caption("Run compliance checks after trade execution — breach detection, reporting deadlines, wash trades.")

with st.form("post_trade_form"):
    st.subheader("Executed Trade Details")

    col1, col2, col3 = st.columns(3)
    with col1:
        order_id        = st.text_input("Order ID", value=f"ORD-{datetime.utcnow().strftime('%H%M%S')}")
        portfolio_id    = st.selectbox("Portfolio", ["FUND-USA-01", "FUND-EMEA-01", "FUND-BOND-01"])
        ticker          = st.text_input("Ticker", value="AAPL")
        security_id     = st.text_input("Security ID", value="AAPL")

    with col2:
        asset_class     = st.selectbox("Asset Class", ["EQUITY", "BOND", "DERIVATIVE", "FX", "COMMODITY", "ETF"])
        side            = st.selectbox("Side", ["BUY", "SELL", "SHORT", "COVER"])
        currency        = st.selectbox("Currency", ["USD", "EUR", "GBP"])
        jurisdiction    = st.selectbox("Fund Jurisdiction", ["USA", "EMEA", "APAC"])

    with col3:
        quantity         = st.number_input("Quantity", min_value=1, value=10000, step=100)
        price            = st.number_input("Order Price", min_value=0.01, value=185.50, format="%.2f")
        execution_price  = st.number_input("Execution Price", min_value=0.01, value=185.45, format="%.2f")
        broker_id        = st.selectbox("Broker", ["GOLDMAN", "MORGAN_STANLEY", "JPMORGAN", "UBS", "DB", "UNKNOWN_BROKER"])
        trader_id        = st.text_input("Trader ID", value="T001")

    st.divider()
    st.subheader("Post-Trade Context")
    col4, col5 = st.columns(2)
    with col4:
        reporting_delay_min   = st.number_input("TRACE Reporting Delay (minutes)", min_value=0, value=0)
        mifid_delay_hours     = st.number_input("MiFID II Reporting Delay (hours)", min_value=0, value=0)
        emir_delay_hours      = st.number_input("EMIR Reporting Delay (hours)", min_value=0, value=0)
        fail_to_deliver_days  = st.number_input("Fail-to-Deliver Days (Reg SHO)", min_value=0, value=0)

    with col5:
        recent_opposite_trade = st.text_input("Recent Opposite Trade ID (Wash Trade)", value="")
        is_quarter_end        = st.checkbox("Quarter-End (13F trigger)")
        is_13f_filer          = st.checkbox("13F Filer (>$100M AUM)")
        is_sftr               = st.checkbox("Securities Financing Transaction (SFTR)")
        sftr_delay_hours      = st.number_input("SFTR Reporting Delay (hours)", min_value=0, value=0)

    submitted = st.form_submit_button("Run Post-Trade Check", type="primary", use_container_width=True)

if submitted:
    payload = {
        "order_id": order_id,
        "portfolio_id": portfolio_id,
        "security_id": security_id,
        "ticker": ticker,
        "asset_class": asset_class,
        "side": side,
        "quantity": float(quantity),
        "price": float(price),
        "currency": currency,
        "trader_id": trader_id,
        "fund_jurisdiction": jurisdiction,
        "execution_price": float(execution_price),
        "execution_time": datetime.utcnow().isoformat(),
        "broker_id": broker_id,
    }

    with st.spinner("Running post-trade checks..."):
        try:
            result = post_sync("/compliance/post-trade", payload)
        except Exception as e:
            st.error(f"API error: {e}")
            st.stop()

    status = result.get("status", "UNKNOWN")
    passed = result.get("passed", False)

    if passed:
        st.success(f"✅ **{status}** — Trade passed all post-trade compliance checks")
    else:
        st.error(f"🚫 **{status}** — Post-trade breach detected. Immediate action required.")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Status", status)
    m2.metric("Violations", len(result.get("violations", [])))
    m3.metric("Warnings", len(result.get("warnings", [])))
    m4.metric("Rules Checked", len(result.get("checked_rules", [])))

    violations = result.get("violations", [])
    if violations:
        st.subheader("🚫 Post-Trade Violations")
        for v in violations:
            with st.expander(f"[{v['rule_id']}] {v['rule_name']}", expanded=True):
                st.error(v["message"])
                cols = st.columns(2)
                cols[0].write(f"**Jurisdiction:** {v.get('jurisdiction', '-')}")
                cols[1].write(f"**Regulation:** {v.get('regulation_ref', '-')}")

    warnings = result.get("warnings", [])
    if warnings:
        st.subheader("⚠️ Warnings")
        for w in warnings:
            with st.expander(f"[{w['rule_id']}] {w['rule_name']}"):
                st.warning(w["message"])
                if w.get("regulation_ref"):
                    st.caption(f"Regulation: {w['regulation_ref']}")

    if passed and not warnings:
        st.info("Trade is fully compliant. No post-trade issues detected.")

    with st.expander("Raw JSON Response"):
        st.json(result)
