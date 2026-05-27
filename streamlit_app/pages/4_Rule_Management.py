import streamlit as st
import pandas as pd
from streamlit_app.utils.api_client import get_sync

st.set_page_config(page_title="Rule Management", page_icon="📜", layout="wide")
st.title("📜 Rule Management")
st.caption(
    "View all active compliance rules across jurisdictions. "
    "Rules are managed in [DecisionRules.io](https://decisionrules.io) or the local rule engine."
)

# ── Load Rules ───────────────────────────────────────────────────────────────
try:
    all_rules = get_sync("/rules/")
except Exception as e:
    st.error(f"Could not connect to API: {e}")
    st.stop()

# ── Summary ──────────────────────────────────────────────────────────────────
corp_rules = all_rules.get("corporate", {}).get("rules", [])
usa_rules  = all_rules.get("usa", {}).get("rules", [])
emea_rules = all_rules.get("emea", {}).get("rules", [])

c1, c2, c3, c4 = st.columns(4)
c1.metric("Corporate Rules", len(corp_rules))
c2.metric("USA Rules", len(usa_rules))
c3.metric("EMEA Rules", len(emea_rules))
c4.metric("Total Rules", len(corp_rules) + len(usa_rules) + len(emea_rules))

st.divider()

# ── Tabs per Jurisdiction ────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs(["🏢 Corporate", "🇺🇸 USA", "🇪🇺 EMEA", "🔍 Search All"])

def render_rules_table(rules: list[dict]):
    if not rules:
        st.info("No rules found.")
        return

    df = pd.DataFrame(rules)
    severity_color = {"BLOCK": "🔴", "WARNING": "🟡", "INFO": "🔵"}
    phase_icon     = {"PRE": "⬅️ Pre-Trade", "POST": "➡️ Post-Trade"}

    if "severity" in df.columns:
        df["Severity"] = df["severity"].map(lambda s: f"{severity_color.get(s, '')} {s}")
    if "phase" in df.columns:
        df["Phase"] = df["phase"].map(lambda p: phase_icon.get(p, p))

    display_cols = []
    rename = {}
    if "id" in df.columns:        display_cols.append("id");        rename["id"] = "Rule ID"
    if "name" in df.columns:      display_cols.append("name");      rename["name"] = "Rule Name"
    if "Severity" in df.columns:  display_cols.append("Severity")
    if "Phase" in df.columns:     display_cols.append("Phase")
    if "regulation" in df.columns: display_cols.append("regulation"); rename["regulation"] = "Regulation"

    display_df = df[display_cols].rename(columns=rename)
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    # Block vs Warning breakdown
    if "severity" in df.columns:
        col_a, col_b = st.columns(2)
        col_a.metric("BLOCK rules", len(df[df["severity"] == "BLOCK"]))
        col_b.metric("WARNING rules", len(df[df["severity"] == "WARNING"]))


with tab1:
    st.subheader("Corporate Restrictions")
    st.markdown(all_rules.get("corporate", {}).get("description", ""))
    st.markdown("""
    **Applies to:** All portfolios regardless of jurisdiction.
    Covers firm-wide policies: restricted/watch lists, blackout periods,
    mandate compliance, concentration limits, Chinese walls, and P&L stops.
    """)
    render_rules_table(corp_rules)


with tab2:
    st.subheader("USA Regulatory Rules")
    st.markdown(all_rules.get("usa", {}).get("description", ""))
    st.markdown("""
    **Applies to:** USA-jurisdiction portfolios.

    | Regulation | Coverage |
    |-----------|----------|
    | SEC Rule 10b-5 / Rule 144 | Insider trading, restricted securities |
    | Regulation SHO | Short selling locate & close-out |
    | Regulation T | Margin requirements (50% initial) |
    | Rule 13D/G, Section 16 | Beneficial ownership thresholds |
    | Investment Company Act | Diversification (5%/25% tests) |
    | Volcker Rule | Proprietary trading ban for banks |
    | FINRA PDT Rule | Pattern day trader restrictions |
    | CFTC Part 150 | Commodity derivative position limits |
    | Regulation NMS | Best execution |
    | FINRA TRACE | Bond trade reporting (15-min) |
    | SEC Rule 13F | Institutional manager reporting |
    """)
    render_rules_table(usa_rules)


with tab3:
    st.subheader("EMEA Regulatory Rules")
    st.markdown(all_rules.get("emea", {}).get("description", ""))
    st.markdown("""
    **Applies to:** EMEA-jurisdiction portfolios (EU + UK).

    | Regulation | Coverage |
    |-----------|----------|
    | MAR (EU 596/2014) | Insider trading, market manipulation, STR |
    | EU Short Selling Reg | Net short notifications (0.1%, 0.5%) |
    | MiFID II Art. 27/57 | Best execution, commodity position limits |
    | MiFID II Art. 26 | T+1 transaction reporting |
    | EMIR (EU 648/2012) | Derivative clearing & reporting |
    | UCITS (2009/65/EC) | 5% issuer, 40% bucket rules |
    | AIFMD (2011/61/EU) | Leverage limits |
    | UK FCA DTR 5 | UK major shareholding (3% threshold) |
    | EU Transparency Dir. | EU shareholding notification (5%+) |
    | SFDR (2019/2088) | ESG score thresholds (Art. 8/9) |
    | SFTR (2015/2365) | Securities financing T+1 reporting |
    """)
    render_rules_table(emea_rules)


with tab4:
    st.subheader("Search All Rules")
    search = st.text_input("Search by rule ID, name, or regulation", placeholder="e.g. MAR, BLOCK, 13D...")

    all_combined = (
        [{"jurisdiction": "CORPORATE", **r} for r in corp_rules]
        + [{"jurisdiction": "USA", **r} for r in usa_rules]
        + [{"jurisdiction": "EMEA", **r} for r in emea_rules]
    )

    if search:
        s = search.lower()
        filtered = [
            r for r in all_combined
            if s in r.get("id", "").lower()
            or s in r.get("name", "").lower()
            or s in r.get("regulation", "").lower()
            or s in r.get("severity", "").lower()
            or s in r.get("jurisdiction", "").lower()
        ]
    else:
        filtered = all_combined

    st.caption(f"Showing {len(filtered)} of {len(all_combined)} rules")
    render_rules_table(filtered)

# ── DecisionRules.io Integration Info ────────────────────────────────────────
st.divider()
st.subheader("DecisionRules.io Integration")
st.markdown("""
To manage rules via the DecisionRules.io no-code platform:

1. Sign up at [decisionrules.io](https://decisionrules.io)
2. Import the JSON configs from `decision_rules_config/` folder
3. Copy your **API Key** and **Rule IDs** into your `.env` file
4. The engine will automatically use DecisionRules.io when configured

**Benefits of DecisionRules.io:**
- No-code rule editing via UI (business users can modify rules)
- Version control & rollback
- A/B testing of rule sets
- Audit trail of rule changes
- MCP integration for AI assistants
- Real-time rule deployment without restart

**MCP (Model Context Protocol) Integration:**
DecisionRules.io supports MCP servers, allowing AI assistants (Claude, GPT-4) to:
- Query which rules apply to a given trade
- Explain why a trade was blocked
- Suggest rule modifications
""")

with st.expander("View .env configuration template"):
    st.code("""
# Add to your .env file
DECISION_RULES_API_KEY=your-api-key-here
DR_RULE_ID_PRE_TRADE_CORPORATE=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DR_RULE_ID_PRE_TRADE_USA=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DR_RULE_ID_PRE_TRADE_EMEA=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DR_RULE_ID_POST_TRADE_CORPORATE=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DR_RULE_ID_POST_TRADE_USA=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
DR_RULE_ID_POST_TRADE_EMEA=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    """, language="bash")
