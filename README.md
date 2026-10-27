# Insurance Claim Processing Agent — LangGraph

## Objective
AI-powered insurance claim workflow using LangGraph and GPT-4o-mini.

## Architecture

```text
                         START
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
 Document Verification  Eligibility       Fraud Detection
        |                  |                  |
        +------------------+------------------+
                           |
                           v
                    Claim Summary
                           |
                    Conditional Router
                 /          |          \
                /           |           \
               v            v            v
        AUTO APPROVE      REJECT      HUMAN REVIEW
                                             |
                                             v
                                      Human Approval
```

## Required technical concepts

- LangGraph
- GPT-4o-mini
- 5+ workflow agents/nodes
- Parallel verification, eligibility and fraud branches
- Conditional routing
- Human-in-the-loop
- Streamlit

## Installation with Anaconda

```bash
conda create -n insurance_ai python=3.11 -y
conda activate insurance_ai
cd /d D:\EICT_AI_DS_ML\Python\Practice_work\Capstone3\Insurance_Claim_Processing_Agent
pip install -r requirements.txt
```

Create `.env` from `.env.example` and add your API key.

Run:

```bash
streamlit run app.py
```

## Demo scenarios

### 1. Complete claim
- Policy: Active
- Amount: 25,000
- Required documents: all present
- Fraud risk: LOW
- Expected: AUTO APPROVE

### 2. Missing documents
- Policy: Active
- Amount: 25,000
- Remove Claim Form or Incident Report from uploaded/manual documents
- Expected: REJECT

### 3. Suspicious/high-value claim
- Policy: Active
- Amount: 150,000
- Complete documents
- Expected: HUMAN REVIEW

### 4. Expired policy
- Policy: Expired
- Expected: REJECT

### 5. High-value valid claim
- Policy: Active
- Amount: 100,000+
- Complete documents
- Expected: HUMAN REVIEW

## Important implementation note

The three initial checks are modeled as independent LangGraph branches from START. They converge at the claim summary node. The router then uses conditional edges to select approval, rejection, or human review.

The application is a workflow/orchestration demonstration and should not be used to make real insurance decisions without appropriate human governance, validation, audit controls, and regulatory review.
