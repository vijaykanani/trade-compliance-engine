import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from streamlit_app.utils.api_client import get_sync, post_sync
from streamlit_app.demo_auth import require_demo_access

st.set_page_config(page_title="Breach Dashboard", page_icon="📊", layout="wide")
require_demo_access()
st.title("📊 Compliance Breach Dashboard")
st.caption("Monitor, investigate, and resolve compliance breaches.")

# ── Stats ────────────────────────────────────────────────────────────────────
try:
    stats = get_sync("/compliance/stats")
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Checks", stats.get("total_checks", 0))
    col2.metric("Approved", stats.get("approved", 0), delta_color="normal")
    col3.metric("Blocked", stats.get("blocked", 0), delta_color="inverse")
    col4.metric("Unresolved Breaches", stats.get("unresolved_breaches", 0), delta_color="inverse")
    col5.metric("Block Rate", f"{stats.get('block_rate_pct', 0):.1f}%")
except Exception as e:
    st.warning(f"Could not load stats: {e}")
    stats = {}

st.divider()

# ── Filters ──────────────────────────────────────────────────────────────────
col_f1, col_f2, col_f3 = st.columns([2, 2, 1])
with col_f1:
    portfolio_filter = st.selectbox("Filter by Portfolio", ["All", "FUND-USA-01", "FUND-EMEA-01", "FUND-BOND-01"])
with col_f2:
    check_type_filter = st.selectbox("Check Type", ["All", "PRE_TRADE", "POST_TRADE"])
with col_f3:
    limit = st.number_input("Max Records", min_value=10, max_value=500, value=50)

# ── Fetch Breaches ────────────────────────────────────────────────────────────
params = {"limit": limit}
if portfolio_filter != "All":
    params["portfolio_id"] = portfolio_filter
if check_type_filter != "All":
    params["check_type"] = check_type_filter

try:
    breaches = get_sync("/compliance/breaches", params)
except Exception as e:
    st.error(f"Could not load breaches: {e}")
    breaches = []

if not breaches:
    st.info("No compliance records found. Run some pre/post trade checks first.")
    st.stop()

# ── Build DataFrame ──────────────────────────────────────────────────────────
rows = []
for b in breaches:
    viols = b.get("violations", [])
    warns = b.get("warnings", [])
    rows.append({
        "ID": b["id"][:8] + "...",
        "Full ID": b["id"],
        "Order ID": b["order_id"],
        "Portfolio": b["portfolio_id"],
        "Ticker": b["ticker"],
        "Trader": b["trader_id"],
        "Type": b["check_type"],
        "Source": b["rule_source"],
        "Status": b["status"],
        "Passed": "✅" if b["passed"] else "🚫",
        "Violations": len(viols),
        "Warnings": len(warns),
        "Top Violation": viols[0]["rule_id"] if viols else (warns[0]["rule_id"] if warns else "-"),
        "Timestamp": b["timestamp"][:19].replace("T", " "),
        "Resolved": "✅" if b["resolved"] else "❌",
    })

df = pd.DataFrame(rows)

# ── Charts ───────────────────────────────────────────────────────────────────
ch1, ch2 = st.columns(2)

with ch1:
    status_counts = df["Status"].value_counts().reset_index()
    status_counts.columns = ["Status", "Count"]
    color_map = {"APPROVED": "#2ECC71", "BLOCKED": "#E74C3C", "WARNING": "#F39C12"}
    fig = px.pie(status_counts, names="Status", values="Count",
                 color="Status", color_discrete_map=color_map,
                 title="Check Results Distribution")
    st.plotly_chart(fig, use_container_width=True)

with ch2:
    type_counts = df["Type"].value_counts().reset_index()
    type_counts.columns = ["Type", "Count"]
    fig2 = px.bar(type_counts, x="Type", y="Count",
                  color="Type", title="Pre vs Post Trade Checks",
                  color_discrete_map={"PRE_TRADE": "#3498DB", "POST_TRADE": "#9B59B6"})
    st.plotly_chart(fig2, use_container_width=True)

# ── Table ────────────────────────────────────────────────────────────────────
st.subheader("Compliance Log")

display_cols = ["Passed", "Order ID", "Portfolio", "Ticker", "Trader", "Type",
                "Status", "Violations", "Warnings", "Top Violation", "Timestamp", "Resolved"]
st.dataframe(
    df[display_cols],
    use_container_width=True,
    hide_index=True,
    column_config={
        "Passed": st.column_config.TextColumn("✓", width="small"),
        "Violations": st.column_config.NumberColumn("Violations", format="%d"),
        "Warnings": st.column_config.NumberColumn("Warnings", format="%d"),
    },
)

# ── Breach Detail & Resolve ──────────────────────────────────────────────────
st.divider()
st.subheader("Breach Detail & Resolution")

unresolved = [b for b in breaches if not b["passed"] and not b["resolved"]]
if not unresolved:
    st.success("No unresolved breaches.")
else:
    breach_options = {f"{b['order_id']} | {b['ticker']} | {b['timestamp'][:19]}": b for b in unresolved}
    selected_label = st.selectbox("Select a breach to investigate:", list(breach_options.keys()))
    selected = breach_options[selected_label]

    col_d1, col_d2 = st.columns(2)
    with col_d1:
        st.write(f"**Order:** {selected['order_id']}")
        st.write(f"**Portfolio:** {selected['portfolio_id']}")
        st.write(f"**Trader:** {selected['trader_id']}")
        st.write(f"**Check Type:** {selected['check_type']}")

    with col_d2:
        st.write(f"**Ticker:** {selected['ticker']}")
        st.write(f"**Status:** {selected['status']}")
        st.write(f"**Rule Source:** {selected['rule_source']}")

    for v in selected.get("violations", []):
        st.error(f"🚫 [{v['rule_id']}] {v['rule_name']}: {v['message']}")
    for w in selected.get("warnings", []):
        st.warning(f"⚠️ [{w['rule_id']}] {w['rule_name']}: {w['message']}")

    with st.form("resolve_form"):
        resolved_by = st.text_input("Resolved By (Compliance Officer ID)")
        notes = st.text_area("Resolution Notes")
        resolve_btn = st.form_submit_button("Mark as Resolved", type="primary")

    if resolve_btn and resolved_by:
        try:
            post_sync(
                f"/compliance/breaches/{selected['id']}/resolve",
                {"resolved_by": resolved_by, "notes": notes},
            )
            st.success("Breach marked as resolved.")
            st.rerun()
        except Exception as e:
            st.error(f"Could not resolve: {e}")
