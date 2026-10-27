# Test Cases

## Test Case 1 — Complete Claim → Auto Approve

Claim ID: CLM-1001
Policy: POL-5001
Policy Status: Active
Claim Amount: 25,000

Required documents:
- Policy Document
- Claim Form
- Incident Report
- Identity Proof
- Repair Estimate

Expected:
AUTO APPROVE

## Test Case 2 — Missing Required Document → Reject

Claim ID: CLM-1002
Policy: POL-5002
Policy Status: Active
Claim Amount: 20,000

Remove:
- Incident Report

Expected:
REJECT

## Test Case 3 — Suspicious / High-Value Claim → Human Review

Claim ID: CLM-1003
Policy: POL-5003
Policy Status: Active
Claim Amount: 150,000

All documents present.

Expected:
HUMAN REVIEW

## Test Case 4 — Expired Policy → Reject

Claim ID: CLM-1004
Policy: POL-5004
Policy Status: Expired
Claim Amount: 30,000

Expected:
REJECT

## Test Case 5 — High-Value Valid Claim → Human Review

Claim ID: CLM-1005
Policy: POL-5005
Policy Status: Active
Claim Amount: 100,000

All documents present.

Expected:
HUMAN REVIEW
