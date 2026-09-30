import streamlit as st
from streamlit_app.demo_auth import render_demo_page_link, require_demo_access

st.set_page_config(
    page_title="Trade Compliance Command Center",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)
require_demo_access()

st.title("⚖️ Trade Compliance Command Center")
st.subheader("Enterprise pre-trade, post-trade, and market risk monitoring")

st.markdown(
    """
    This operating layer covers public markets, private markets, digital assets, and AI governance with configurable controls,
    override workflows, audit history, and API-driven integration for downstream systems.
    """
)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Coverage", "7", "Rule domains")
k2.metric("Active rules", "42", "Across all domains")
k3.metric("Breach rate", "11.8%", "Last 30 days")
k4.metric("Override approvals", "24", "Reviewed and tracked")

st.divider()

nav = st.columns(4)
with nav[0]:
    render_demo_page_link("/Pre_Trade_Check", "🔎 Pre-Trade Check")
with nav[1]:
    render_demo_page_link("/Post_Trade_Check", "📋 Post-Trade Check")
with nav[2]:
    render_demo_page_link("/Breach_Dashboard", "📊 Breach Dashboard")
with nav[3]:
    render_demo_page_link("/Rule_Management", "📜 Rule Management")

render_demo_page_link("/Domain_Workflows", "🧭 Domain Compliance Workflows")

st.divider()

cover_cols = st.columns(4)
with cover_cols[0]:
    st.markdown("### Public Markets")
    st.write("Equities, fixed income, derivatives, ETFs, FX, listed funds, and exchange rule surveillance.")
with cover_cols[1]:
    st.markdown("### Private Markets")
    st.write("Deal approval, investor eligibility, diligence, side letters, transfer consent, concentration, and valuation review.")
with cover_cols[2]:
    st.markdown("### Digital Assets")
    st.write("Wallet and counterparty screening, token review, jurisdiction support, Travel Rule, custody, and protocol risk.")
with cover_cols[3]:
    st.markdown("### AI Governance")
    st.write("Use-case intake, risk classification, data rights, validation, fairness, human oversight, and monitoring.")

st.caption("All product domains are enabled in this demonstration. Entitlement-based visibility can be connected when a license source is configured.")

st.divider()

st.subheader("Operational control areas")
left, center, right = st.columns(3)
with left:
    st.markdown("**Policy & Rule Architecture**")
    st.write("- Corporate restrictions")
    st.write("- USA / EMEA coverage")
    st.write("- Public and private market controls")
    st.write("- Digital assets and AI governance")
with center:
    st.markdown("**Override & Accountability**")
    st.write("- Human override with notes")
    st.write("- Full history tracking")
    st.write("- Escalation route for high-risk exceptions")
with right:
    st.markdown("**System Integration**")
    st.write("- CSV import / export")
    st.write("- Automated compliance run trigger")
    st.write("- API-driven order and breach exchange")

st.divider()

st.subheader("Key control themes")
summary = st.tabs(["Controls", "Data flow", "Reporting"])
with summary[0]:
    st.markdown(
        """
        - Restricted list and watch list checks\n
        - Position, concentration, and mandate controls\n
        - Sanctions, AML, and custody checks\n
        - AI governance and model risk controls\n
        """
    )
with summary[1]:
    st.markdown(
        """
        - Order intake through UI or API\n
        - Trade validation and breach scoring\n
        - Override records and decision history\n
        - Data export for review and downstream processing\n
        """
    )
with summary[2]:
    st.markdown(
        """
        - Breach dashboard and trend monitoring\n
        - Exportable CSV and JSON evidence packs\n
        - Compliance exception register\n
        """
    )
