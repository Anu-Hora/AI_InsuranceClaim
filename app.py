import json
import os
import streamlit as st
from dotenv import load_dotenv
from claim_graph import process_claim

load_dotenv()

st.set_page_config(page_title="Insurance Claim Processing Agent", page_icon="🛡️", layout="wide")
st.title("Insurance Claim Processing Agent")
st.caption("LangGraph + GPT-4o-mini | Parallel verification, eligibility and fraud checks | Human-in-the-loop")

with st.sidebar:
    st.header("Configuration")
    model = st.text_input("OpenAI Model", os.getenv("OPENAI_MODEL", "gpt-4o-mini"))
    st.info("The workflow uses LangGraph nodes and conditional routing. High-risk or uncertain claims are routed to human approval.")

if not os.getenv("OPENAI_API_KEY"):
    st.warning("OPENAI_API_KEY is not configured. Add it to the .env file before processing claims.")

st.subheader("Claim Details")
c1, c2 = st.columns(2)
with c1:
    claim_id = st.text_input("Claim ID", "CLM-1001")
    policy_number = st.text_input("Policy Number", "POL-5001")
    claimant_name = st.text_input("Claimant Name", "Rahul Sharma")
    claim_type = st.selectbox("Claim Type", ["Health", "Motor", "Travel", "Property"])
with c2:
    claim_amount = st.number_input("Claim Amount", min_value=0.0, value=25000.0, step=1000.0)
    policy_status = st.selectbox("Policy Status", ["Active", "Expired"])
    incident_date = st.date_input("Incident Date")
    policy_end_date = st.date_input("Policy End Date")

st.subheader("Supporting Documents")
uploaded = st.file_uploader(
    "Upload supporting documents",
    type=["pdf", "txt", "docx"],
    accept_multiple_files=True
)

default_docs = st.text_area(
    "Or enter document names manually",
    value="Policy Document\nClaim Form\nIncident Report\nIdentity Proof\nRepair Estimate"
)

document_text = ""
if uploaded:
    st.write("Uploaded files:", ", ".join(f.name for f in uploaded))
    for f in uploaded:
        try:
            document_text += f"\n--- {f.name} ---\n" + f.read().decode("utf-8", errors="ignore")
        except Exception:
            document_text += f"\n--- {f.name} ---\n"

extra_notes = st.text_area(
    "Additional claim information / notes",
    "Claim submitted within policy period. No previous claims mentioned."
)

if st.button("Process Claim", type="primary", use_container_width=True):
    claim = {
        "claim_id": claim_id,
        "policy_number": policy_number,
        "claimant_name": claimant_name,
        "claim_type": claim_type,
        "claim_amount": claim_amount,
        "policy_status": policy_status,
        "incident_date": str(incident_date),
        "policy_end_date": str(policy_end_date),
        "required_documents": [x.strip() for x in default_docs.splitlines() if x.strip()],
        "uploaded_document_names": [f.name for f in uploaded] if uploaded else [],
        "document_text": document_text,
        "notes": extra_notes,
    }

    with st.spinner("Running LangGraph claim workflow..."):
        try:
            result = process_claim(claim, model=model)
        except Exception as e:
            st.error(f"Processing failed: {e}")
            st.stop()

    decision = result.get("final_decision", "UNKNOWN")
    color = {"AUTO APPROVE": "🟢", "REJECT": "🔴", "HUMAN REVIEW": "🟠"}.get(decision, "⚪")
    st.header(f"{color} Final Decision: {decision}")

    a, b, c = st.columns(3)
    with a:
        st.metric("Fraud Risk", result.get("fraud_risk", "N/A"))
    with b:
        st.metric("Eligibility", result.get("eligibility", "N/A"))
    with c:
        st.metric("Documents", result.get("documents_status", "N/A"))

    st.subheader("Claim Summary")
    st.write(result.get("claim_summary", ""))

    st.subheader("Decision Justification")
    st.write(result.get("decision_reason", ""))

    if decision == "HUMAN REVIEW":
        st.warning("This claim requires human approval because it is high-risk, uncertain, high-value, or otherwise unsuitable for automatic processing.")
        st.subheader("Human Approval")
        human_decision = st.radio("Reviewer decision", ["Pending", "Approve", "Reject"])
        reviewer_notes = st.text_area("Reviewer notes")
        if human_decision != "Pending":
            st.success(f"Human reviewer selected: {human_decision}")
            st.write(reviewer_notes)

    with st.expander("Document Verification"):
        st.json(result.get("document_check", {}))
    with st.expander("Eligibility Check"):
        st.json(result.get("eligibility_check", {}))
    with st.expander("Fraud Detection"):
        st.json(result.get("fraud_check", {}))
    with st.expander("Complete LangGraph State"):
        st.json(result)

    st.download_button(
        "Download Claim Evaluation JSON",
        data=json.dumps(result, indent=2),
        file_name=f"{claim_id}_evaluation.json",
        mime="application/json",
    )
