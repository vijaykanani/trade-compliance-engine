import streamlit as st
import pandas as pd
from streamlit_app.rule_store import create_rule, delete_rule, load_audit_log, load_rule_registry
from streamlit_app.utils.api_client import get_sync
from streamlit_app.demo_auth import require_demo_access

st.set_page_config(page_title="Rule Management", page_icon="📜", layout="wide")
require_demo_access()
st.title("📜 Rule Management")
st.caption("Enterprise rule catalogue, override tracking, and operational control administration.")

GROUPS = {
    "corporate": "Corporate",
    "usa": "USA",
    "emea": "EMEA",
    "public_markets": "Public Markets",
    "private_markets": "Private Markets",
    "digital_assets": "Digital Assets",
    "ai_governance": "AI Governance",
}


def build_rule_dataframe(all_rules: dict) -> pd.DataFrame:
    rows = []
    for group_key, payload in all_rules.items():
        if not isinstance(payload, dict):
            continue
        for rule in payload.get("rules", []):
            record = dict(rule)
            record["jurisdiction"] = GROUPS.get(group_key, group_key.replace("_", " ").title())
            record["active"] = bool(rule.get("active", True))
            record["notes"] = rule.get("notes", "")
            rows.append(record)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    for column in ["id", "name", "jurisdiction", "severity", "phase", "regulation", "notes"]:
        if column not in df.columns:
            df[column] = ""
    df["active"] = df["active"].fillna(True).astype(bool)
    return df


try:
    all_rules = get_sync("/rules/")
except Exception as e:
    st.error(f"Could not connect to API: {e}")
    st.stop()

rule_df = build_rule_dataframe(all_rules)
summary_counts = {label: len(all_rules.get(key, {}).get("rules", [])) for key, label in GROUPS.items()}

c1, c2, c3, c4 = st.columns(4)
c1.metric("Corporate", summary_counts.get("Corporate", 0))
c2.metric("USA", summary_counts.get("USA", 0))
c3.metric("EMEA", summary_counts.get("EMEA", 0))
c4.metric("Total Rules", sum(summary_counts.values()))

st.divider()
with st.sidebar:
    st.subheader("Filters")
    search = st.text_input("Search rules", placeholder="ID, name, regulation...")
    jurisdictions = st.multiselect(
        "Jurisdiction",
        options=sorted(rule_df["jurisdiction"].dropna().unique().tolist()),
        default=sorted(rule_df["jurisdiction"].dropna().unique().tolist()),
    )
    phases = st.multiselect(
        "Phase",
        options=sorted(rule_df["phase"].dropna().unique().tolist()),
        default=sorted(rule_df["phase"].dropna().unique().tolist()),
    )
    severities = st.multiselect(
        "Severity",
        options=sorted(rule_df["severity"].dropna().unique().tolist()),
        default=sorted(rule_df["severity"].dropna().unique().tolist()),
    )
    show_inactive = st.checkbox("Include inactive rules", value=True)

filtered_df = rule_df.copy()
if jurisdictions:
    filtered_df = filtered_df[filtered_df["jurisdiction"].isin(jurisdictions)]
if phases:
    filtered_df = filtered_df[filtered_df["phase"].isin(phases)]
if severities:
    filtered_df = filtered_df[filtered_df["severity"].isin(severities)]
if search:
    needle = search.lower()
    filtered_df = filtered_df[
        filtered_df["id"].astype(str).str.lower().str.contains(needle, na=False)
        | filtered_df["name"].astype(str).str.lower().str.contains(needle, na=False)
        | filtered_df["regulation"].astype(str).str.lower().str.contains(needle, na=False)
    ]
if not show_inactive:
    filtered_df = filtered_df[filtered_df["active"] == True]

st.caption(f"Showing {len(filtered_df)} rules")

editable = filtered_df[["jurisdiction", "id", "name", "phase", "severity", "regulation", "active", "notes"]].copy()
editable["active"] = editable["active"].astype(bool)

edited = st.data_editor(
    editable,
    use_container_width=True,
    hide_index=True,
    disabled=["jurisdiction", "id", "name", "phase", "severity", "regulation"],
    column_config={
        "active": st.column_config.CheckboxColumn("Active", help="Turn a rule on or off for policy enforcement"),
        "notes": st.column_config.TextColumn("Notes", width="large"),
    },
)

if st.button("Save local rule settings"):
    st.session_state["local_rule_snapshot"] = edited.copy()
    st.success("Local rule changes saved for this session.")

if "local_rule_snapshot" in st.session_state:
    st.info(f"{len(st.session_state['local_rule_snapshot'])} rules are currently persisted in the app session.")

st.divider()

with st.expander("Create a new rule", expanded=True):
    with st.form("create_rule_form"):
        col1, col2 = st.columns(2)
        with col1:
            new_jurisdiction = st.selectbox("Jurisdiction", list(GROUPS.values()))
            new_name = st.text_input("Rule name")
            new_regulation = st.text_input("Regulation")
        with col2:
            new_severity = st.selectbox("Severity", ["BLOCK", "WARNING", "INFO"])
            new_phase = st.selectbox("Phase", ["PRE", "POST"])
            new_notes = st.text_area("Notes")

        submitted = st.form_submit_button("Create rule")
        if submitted:
            if not new_name.strip():
                st.warning("Rule name is required.")
            else:
                registry = load_rule_registry()
                mapped_group = next(key for key, value in GROUPS.items() if value == new_jurisdiction)
                created = create_rule(
                    jurisdiction=mapped_group,
                    name=new_name,
                    regulation=new_regulation or "Internal Policy",
                    severity=new_severity,
                    phase=new_phase,
                    notes=new_notes,
                    registry=registry,
                    registry_path="streamlit_app/rule_registry.json",
                    audit_path="streamlit_app/rule_audit.json",
                )
                st.success(f"Rule {created['id']} created successfully.")
                st.rerun()

with st.expander("Delete an existing rule"):
    deleted_rule_id = st.text_input("Rule ID to remove")
    deleted_jurisdiction = st.selectbox("Jurisdiction", list(GROUPS.values()), key="delete_rule_jurisdiction")
    if st.button("Delete rule"):
        registry = load_rule_registry()
        mapped_group = next(key for key, value in GROUPS.items() if value == deleted_jurisdiction)
        removed = delete_rule(
            jurisdiction=mapped_group,
            rule_id=deleted_rule_id.strip(),
            registry=registry,
            registry_path="streamlit_app/rule_registry.json",
            audit_path="streamlit_app/rule_audit.json",
        )
        if removed:
            st.success(f"Rule {deleted_rule_id.strip()} deleted.")
            st.rerun()
        else:
            st.warning("No matching rule was found for deletion.")

st.divider()

rule_tabs = st.tabs(["Public Markets", "Private Markets", "Digital Assets", "AI Governance", "USA", "EMEA", "Corporate", "Audit Trail"])
for idx, label in enumerate(["Public Markets", "Private Markets", "Digital Assets", "AI Governance", "USA", "EMEA", "Corporate", "Audit Trail"]):
    with rule_tabs[idx]:
        if label == "Audit Trail":
            audit_log = load_audit_log("streamlit_app/rule_audit.json")
            if audit_log:
                st.dataframe(pd.DataFrame(audit_log), use_container_width=True, hide_index=True)
            else:
                st.info("No changes recorded yet.")
            continue

        group_key = next((key for key, value in GROUPS.items() if value == label), None)
        if group_key is None:
            continue
        table = edited[edited["jurisdiction"] == label].copy()
        if table.empty:
            st.info(f"No rules found in {label}.")
        else:
            st.dataframe(table, use_container_width=True, hide_index=True)

st.divider()
st.subheader("In-app rule workflow")
st.markdown(
    """
    1. Review the rule catalogue by market domain and jurisdiction.\n
    2. Search for a rule by ID, name, or regulation.\n
    3. Toggle activation and annotate the operational rationale.\n
    4. Create or remove rules directly from this console.\n
    5. Review the audit trail for all rule changes and decisions.\n
    """
)
