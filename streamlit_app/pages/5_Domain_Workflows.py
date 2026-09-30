import json

import pandas as pd
import streamlit as st

from streamlit_app.domain_workflows import DOMAIN_RULES, load_assessments, save_assessment
from streamlit_app.demo_auth import render_demo_page_link, require_demo_access

st.set_page_config(page_title="Domain Compliance Workflows", page_icon="🧭", layout="wide")
require_demo_access()
st.title("🧭 Domain Compliance Workflows")
st.caption("Lifecycle assessments for private investments, digital-asset activities, and AI systems. Public-market order workflows remain separate.")
st.info("Control prompts are configurable decision support. Applicability and legal thresholds must be set for each licensed product, jurisdiction, and client mandate.")

tabs = st.tabs(["Public Markets", "Private Markets", "Digital Assets", "AI Governance", "Assessment History"])


def show_result(record: dict) -> None:
    status = record["status"]
    if status == "APPROVED":
        st.success(f"{status}: no outstanding control findings.")
    elif status == "BLOCKED":
        st.error(f"{status}: resolve blocking findings before proceeding.")
    else:
        st.warning(f"{status}: compliance review is required before proceeding.")
    st.caption(f"Assessment {record['assessment_id']} · {len(record['checked_rules'])} controls evaluated")
    for finding in record["findings"]:
        message = f"[{finding['rule_id']}] {finding['rule_name']} — {finding['message']} Reference: {finding['reference']}"
        (st.error if finding["severity"] == "BLOCK" else st.warning)(message)


with tabs[0]:
    st.subheader("Public-market trading lifecycle")
    st.write("Listed equities, fixed income, ETFs, FX, commodities, and derivatives use order-based pre-trade and executed-trade post-trade checks.")
    public_nav = st.columns(2)
    with public_nav[0]:
        render_demo_page_link("/Pre_Trade_Check", "🔎 Open pre-trade check")
    with public_nav[1]:
        render_demo_page_link("/Post_Trade_Check", "📋 Open post-trade check")
    st.markdown("**Lifecycle controls**")
    st.write("Mandate and restricted-list checks · position and concentration limits · short-sale and locate checks · market-abuse surveillance · execution and regulatory reporting")

with tabs[1]:
    st.subheader("Private investment lifecycle")
    st.write("Assess investment approvals, follow-ons, secondary transfers, capital events, and valuation events against fund terms and investor controls.")
    with st.form("private_assessment"):
        c1, c2, c3 = st.columns(3)
        with c1:
            subject = st.text_input("Deal / asset / event ID", key="prv_subject")
            activity = st.selectbox("Lifecycle activity", ["New investment", "Follow-on investment", "Secondary transfer", "Capital call / distribution", "Valuation event"], key="prv_activity")
            instrument = st.selectbox("Instrument", ["Fund interest", "Private equity", "Private credit", "Real asset", "Structured / other"], key="prv_instrument")
        with c2:
            jurisdiction = st.selectbox("Primary jurisdiction", ["United States", "European Union / EEA", "United Kingdom", "Other / cross-border"], key="prv_jurisdiction")
            investor_type = st.selectbox("Investor classification", ["Institutional", "Professional / qualified", "Retail", "Pending"], key="prv_investor_type")
            commitment = st.number_input("Commitment / transaction value", min_value=0.0, value=0.0, step=100000.0, key="prv_value")
        with c3:
            reviewer = st.text_input("Compliance reviewer", key="prv_reviewer")
            concentration = st.number_input("Post-transaction concentration (%)", min_value=0.0, max_value=100.0, value=0.0, key="prv_concentration")
        st.markdown("**Control evidence**")
        e1, e2, e3 = st.columns(3)
        with e1:
            kyc = st.checkbox("Investor / counterparty due diligence complete", key="prv_kyc")
            eligible = st.checkbox("Eligibility and offering restrictions confirmed", key="prv_eligible")
        with e2:
            docs = st.checkbox("LPA, PPM, subscription docs, and side letters reviewed", key="prv_docs")
            conflicts = st.checkbox("Conflicts assessed and cleared", key="prv_conflicts")
        with e3:
            concentration_reviewed = st.checkbox("Concentration and mandate reviewed", key="prv_conc")
            transfer_approved = st.checkbox("Required transfer consents / ROFR cleared", key="prv_transfer")
            valuation_supported = st.checkbox("Valuation evidence and approval recorded", key="prv_valuation")
        notes = st.text_area("Decision notes / evidence references", key="prv_notes")
        submitted = st.form_submit_button("Run private-markets assessment", type="primary")
    if submitted:
        if not subject.strip() or not reviewer.strip():
            st.warning("Provide an event ID and a compliance reviewer to create an auditable assessment.")
        else:
            facts = {"activity": activity, "instrument": instrument, "jurisdiction": jurisdiction, "investor_type": investor_type, "commitment": commitment, "concentration_pct": concentration, "kyc_complete": kyc, "investor_eligible": eligible, "documents_reviewed": docs, "conflicts_cleared": conflicts, "concentration_reviewed": concentration_reviewed, "transfer_approved": transfer_approved, "valuation_supported": valuation_supported}
            record = save_assessment("private_markets", subject, facts, reviewer, notes)
            show_result(record)

with tabs[2]:
    st.subheader("Digital-asset lifecycle")
    st.write("Assess acquisition, disposal, transfer, custody, staking, issuance, and protocol interactions. These are asset, counterparty, custody, and service controls, not equity order checks.")
    with st.form("digital_assessment"):
        c1, c2, c3 = st.columns(3)
        with c1:
            subject = st.text_input("Transaction / case ID", key="dig_subject")
            activity = st.selectbox("Activity", ["Acquire / dispose", "Wallet transfer", "Custody onboarding", "Staking / lending", "Token issuance", "DeFi / protocol interaction"], key="dig_activity")
            token = st.text_input("Token / asset", key="dig_token")
        with c2:
            network = st.text_input("Network / chain", key="dig_network")
            jurisdiction = st.selectbox("Jurisdiction", ["United States", "European Union / EEA", "United Kingdom", "Other / cross-border"], key="dig_jurisdiction")
            value = st.number_input("Estimated value", min_value=0.0, value=0.0, step=1000.0, key="dig_value")
        with c3:
            wallet = st.text_input("Origin / destination wallet or custodian", key="dig_wallet")
            travel_required = st.selectbox("Travel Rule applicable to this transfer?", ["not applicable", "yes"], key="dig_travel_required")
            reviewer = st.text_input("Compliance reviewer", key="dig_reviewer")
        st.markdown("**Control evidence**")
        e1, e2, e3 = st.columns(3)
        with e1:
            sanctions = st.checkbox("Wallet and counterparty screening clear", key="dig_sanctions")
            wallet_screened = st.checkbox("Wallet exposure / transaction risk screened", key="dig_screened")
        with e2:
            jurisdiction_supported = st.checkbox("Jurisdiction and provider permissions confirmed", key="dig_supported")
            custody = st.checkbox("Custody, segregation, and key controls approved", key="dig_custody")
        with e3:
            travel_complete = st.checkbox("Required originator / beneficiary data exchanged", key="dig_travel_complete")
            token_reviewed = st.checkbox("Token classification and product review complete", key="dig_token_review")
            protocol_reviewed = st.checkbox("Protocol / smart-contract risk review complete", key="dig_protocol")
        notes = st.text_area("Decision notes / evidence references", key="dig_notes")
        submitted = st.form_submit_button("Run digital-assets assessment", type="primary")
    if submitted:
        if not subject.strip() or not reviewer.strip():
            st.warning("Provide a transaction/case ID and a compliance reviewer to create an auditable assessment.")
        else:
            facts = {"activity": activity, "token": token, "network": network, "jurisdiction": jurisdiction, "value": value, "wallet_or_custodian": wallet, "travel_rule_required": travel_required, "sanctions_clear": sanctions, "wallet_screened": wallet_screened, "jurisdiction_supported": jurisdiction_supported, "custody_approved": custody, "travel_rule_complete": travel_complete, "token_reviewed": token_reviewed, "protocol_reviewed": protocol_reviewed}
            record = save_assessment("digital_assets", subject, facts, reviewer, notes)
            show_result(record)

with tabs[3]:
    st.subheader("AI system governance lifecycle")
    st.write("Assess AI use-case intake, model changes, deployment approval, periodic review, and incidents across inventory, data, validation, human oversight, and monitoring.")
    with st.form("ai_assessment"):
        c1, c2, c3 = st.columns(3)
        with c1:
            subject = st.text_input("Model / system ID", key="ai_subject")
            activity = st.selectbox("Governance event", ["New use-case intake", "Material model change", "Production deployment", "Periodic review", "Incident / material failure"], key="ai_activity")
            use_case = st.text_input("Intended purpose", key="ai_use_case")
        with c2:
            risk_tier = st.selectbox("Internal risk tier", ["Prohibited / disallowed", "High", "Medium", "Low", "Unclassified"], key="ai_tier")
            affected_people = st.selectbox("Impact on people / decisions", ["Directly affects individuals", "Supports material decisions", "Internal productivity", "No material impact identified"], key="ai_impact")
            third_party = st.selectbox("Third-party model or provider?", ["no", "yes"], key="ai_third_party")
        with c3:
            business_owner = st.text_input("Business owner", key="ai_owner")
            reviewer = st.text_input("Governance reviewer", key="ai_reviewer")
            deployment = st.selectbox("Deployment status", ["Pre-deployment", "In production", "Paused / retired"], key="ai_deployment")
        st.markdown("**Governance evidence**")
        e1, e2, e3 = st.columns(3)
        with e1:
            risk_classified = st.checkbox("Risk classification and inventory record complete", key="ai_classified")
            use_case_approved = st.checkbox("Use-case screened for prohibited / restricted use", key="ai_use_approved")
            data_cleared = st.checkbox("Data provenance, rights, privacy, and retention cleared", key="ai_data")
        with e2:
            model_validated = st.checkbox("Independent validation and performance testing complete", key="ai_validated")
            fairness_tested = st.checkbox("Bias, fairness, and explainability tests reviewed", key="ai_fairness")
            human_oversight = st.checkbox("Human oversight, appeal, and escalation defined", key="ai_human")
        with e3:
            monitoring_ready = st.checkbox("Monitoring, incident response, and rollback ready", key="ai_monitoring")
            vendor_reviewed = st.checkbox("Provider / third-party due diligence complete", key="ai_vendor")
        notes = st.text_area("Decision notes / evidence references", key="ai_notes")
        submitted = st.form_submit_button("Run AI governance assessment", type="primary")
    if submitted:
        if not subject.strip() or not reviewer.strip():
            st.warning("Provide a model/system ID and a governance reviewer to create an auditable assessment.")
        else:
            facts = {"activity": activity, "use_case": use_case, "risk_tier": risk_tier, "affected_people": affected_people, "third_party": third_party, "business_owner": business_owner, "deployment": deployment, "risk_classified": risk_classified, "use_case_approved": use_case_approved, "data_cleared": data_cleared, "model_validated": model_validated, "fairness_tested": fairness_tested, "human_oversight": human_oversight, "monitoring_ready": monitoring_ready, "vendor_reviewed": vendor_reviewed}
            record = save_assessment("ai_governance", subject, facts, reviewer, notes)
            show_result(record)

with tabs[4]:
    st.subheader("Assessment history")
    assessments = load_assessments()
    if not assessments:
        st.info("No domain assessments have been recorded yet.")
    else:
        history = pd.DataFrame([{key: record.get(key) for key in ["assessment_id", "domain", "subject", "status", "reviewer", "timestamp"]} for record in assessments])
        st.dataframe(history.sort_values("timestamp", ascending=False), use_container_width=True, hide_index=True)
        st.download_button("Export assessment history (JSON)", json.dumps(assessments, indent=2), "domain_assessments.json", "application/json")
        selected = st.selectbox("Assessment detail", options=assessments, format_func=lambda item: f"{item['assessment_id']} · {item['domain']} · {item['subject']}")
        st.json(selected)

st.divider()
st.subheader("Control library")
with st.expander("View controls and regulatory reference points"):
    for domain_key, rules in DOMAIN_RULES.items():
        st.markdown(f"**{domain_key.replace('_', ' ').title()}**")
        st.dataframe(pd.DataFrame(rules), use_container_width=True, hide_index=True)