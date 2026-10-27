import json
import re
from typing import Any, Dict, List, TypedDict
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, START, END

load_dotenv()

class ClaimState(TypedDict, total=False):
    claim: Dict[str, Any]
    document_check: Dict[str, Any]
    eligibility_check: Dict[str, Any]
    fraud_check: Dict[str, Any]
    claim_summary: str
    documents_status: str
    eligibility: str
    fraud_risk: str
    final_decision: str
    decision_reason: str
    human_review_required: bool

def llm(model: str):
    return ChatOpenAI(model=model, temperature=0)

def json_call(model: str, system: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    response = llm(model).invoke([
        SystemMessage(content=system),
        HumanMessage(content=json.dumps(payload, indent=2))
    ])
    text = response.content
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"Expected JSON from model but received: {text}")
    return json.loads(match.group(0))

def document_verification(state: ClaimState, model="gpt-4o-mini"):
    claim = state["claim"]
    result = json_call(model, """
You are the Document Verification Agent for an insurance claim.
Compare required document names against uploaded document names and document text.
Do not invent documents. Mark each required document as PRESENT or MISSING.
Return JSON only:
{
  "status": "COMPLETE" or "MISSING_DOCUMENTS",
  "present_documents": [],
  "missing_documents": [],
  "reason": ""
}
""", claim)
    return {"document_check": result, "documents_status": result["status"]}

def eligibility_check(state: ClaimState, model="gpt-4o-mini"):
    claim = state["claim"]
    result = json_call(model, """
You are the Eligibility Check Agent.
Assess whether the claim is eligible based only on the supplied claim data.
A policy marked Expired should be INELIGIBLE.
If incident date is after policy end date, treat it as INELIGIBLE.
Return JSON only:
{
  "eligibility": "ELIGIBLE" or "INELIGIBLE" or "UNCERTAIN",
  "reason": ""
}
""", claim)
    return {"eligibility_check": result, "eligibility": result["eligibility"]}

def fraud_detection(state: ClaimState, model="gpt-4o-mini"):
    claim = state["claim"]
    result = json_call(model, """
You are the Fraud Detection Agent.
Identify potential fraud indicators from the supplied claim data only.
Examples of indicators: suspiciously high amount, inconsistent dates, contradictory notes,
missing supporting evidence, or unusual claim characteristics.
Do not accuse the claimant of fraud. Return a risk level.
Return JSON only:
{
  "risk": "LOW" or "MEDIUM" or "HIGH" or "UNCERTAIN",
  "indicators": [],
  "reason": ""
}
""", claim)
    return {"fraud_check": result, "fraud_risk": result["risk"]}

def claim_summary(state: ClaimState, model="gpt-4o-mini"):
    payload = {
        "claim": state["claim"],
        "document_check": state.get("document_check", {}),
        "eligibility_check": state.get("eligibility_check", {}),
        "fraud_check": state.get("fraud_check", {})
    }
    response = llm(model).invoke([
        SystemMessage(content="Create a concise factual insurance claim summary using only the supplied information. Do not invent facts."),
        HumanMessage(content=json.dumps(payload, indent=2))
    ])
    return {"claim_summary": response.content}

def route_claim(state: ClaimState):
    if state.get("documents_status") == "MISSING_DOCUMENTS":
        return "reject"
    if state.get("eligibility") == "INELIGIBLE":
        return "reject"
    if state.get("fraud_risk") in ("HIGH", "UNCERTAIN"):
        return "human_review"
    try:
        if float(state["claim"].get("claim_amount", 0)) >= 100000:
            return "human_review"
    except (ValueError, TypeError):
        return "human_review"
    if state.get("eligibility") == "UNCERTAIN":
        return "human_review"
    return "approve"

def auto_approve(state: ClaimState):
    return {
        "final_decision": "AUTO APPROVE",
        "decision_reason": "Required documents are present, the policy is eligible, and no high-risk fraud indicator or high-value escalation threshold was identified."
    }

def reject_claim(state: ClaimState):
    reasons = []
    if state.get("documents_status") == "MISSING_DOCUMENTS":
        reasons.append("required documents are missing")
    if state.get("eligibility") == "INELIGIBLE":
        reasons.append("the policy/incident is not eligible")
    return {
        "final_decision": "REJECT",
        "decision_reason": "; ".join(reasons) if reasons else "Claim failed an automatic validation check."
    }

def human_approval(state: ClaimState):
    return {
        "human_review_required": True,
        "final_decision": "HUMAN REVIEW",
        "decision_reason": "The claim requires human approval because it is high-risk, uncertain, or exceeds the automatic approval amount threshold."
    }

def build_graph(model="gpt-4o-mini"):
    workflow = StateGraph(ClaimState)

    # Parallel branches: all three are downstream of START.
    workflow.add_node("document_verification", lambda s: document_verification(s, model))
    workflow.add_node("eligibility_check", lambda s: eligibility_check(s, model))
    workflow.add_node("fraud_detection", lambda s: fraud_detection(s, model))
    workflow.add_node("claim_summary", lambda s: claim_summary(s, model))
    workflow.add_node("auto_approve", auto_approve)
    workflow.add_node("reject_claim", reject_claim)
    workflow.add_node("human_approval", human_approval)

    workflow.add_edge(START, "document_verification")
    workflow.add_edge(START, "eligibility_check")
    workflow.add_edge(START, "fraud_detection")

    # Summary waits until all three parallel checks have completed.
    workflow.add_edge("document_verification", "claim_summary")
    workflow.add_edge("eligibility_check", "claim_summary")
    workflow.add_edge("fraud_detection", "claim_summary")

    workflow.add_conditional_edges(
        "claim_summary",
        route_claim,
        {
            "approve": "auto_approve",
            "reject": "reject_claim",
            "human_review": "human_approval"
        }
    )
    workflow.add_edge("auto_approve", END)
    workflow.add_edge("reject_claim", END)
    workflow.add_edge("human_approval", END)
    return workflow.compile()

def process_claim(claim: Dict[str, Any], model="gpt-4o-mini"):
    graph = build_graph(model)
    return graph.invoke({"claim": claim})
