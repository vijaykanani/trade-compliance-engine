import streamlit as st

st.set_page_config(
    page_title="Trade Compliance Engine",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("⚖️ Pre & Post Trade Compliance Engine")
st.markdown(
    """
    ### Welcome to the Trade Compliance Rule Engine

    This platform provides automated compliance checks for your trading activity,
    covering **Corporate Restrictions**, **USA regulations** (SEC, FINRA, CFTC),
    and **EMEA regulations** (MiFID II, MAR, EMIR, UCITS, SFDR).

    ---

    | Page | Description |
    |------|-------------|
    | **Pre-Trade Check** | Validate an order before it is placed |
    | **Post-Trade Check** | Run compliance checks after execution |
    | **Breach Dashboard** | Monitor and resolve compliance breaches |
    | **Rule Management** | View all active rules across jurisdictions |

    ---

    **Rule Engine:** Powered by [DecisionRules.io](https://decisionrules.io) with local fallback.
    """
)

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("Jurisdictions", "3", "Corporate + USA + EMEA")
with col2:
    st.metric("Total Rules", "34", "Pre & Post Trade")
with col3:
    st.metric("Regulations", "15+", "SEC, MiFID II, MAR, EMIR...")
