---
title: Insurance Claim Validation
emoji: 🏢
colorFrom: blue
colorTo: green
sdk: docker
pinned: false
tags:
  - openenv
app_port: 7860
---

# Insurance Claim Validation Environment

An OpenEnv-compatible RL environment where an AI agent validates insurance claims, detects fraud, and makes approval decisions. Built for the **Meta PyTorch x Hugging Face OpenEnv Hackathon 2026**.

- **HF Space:** https://huggingface.co/spaces/Sanjan-M/insurance-claim-validation
- **API Docs:** https://sanjan-m-insurance-claim-validation.hf.space/docs
- **GitHub:** https://github.com/msanjan9980-eng/meta-openenv

## Environment Description

Insurance claim validation is a high-stakes real-world task performed daily at every insurance company. An agent receives a partial view of a claim and must gather information, reason about policy rules, detect fraud signals, and reach a correct terminal decision within a limited number of steps.

## Action Space

| Action | Description |
|--------|-------------|
| analyze_claim | Reveals policy details, user history, violation flags |
| detect_fraud_signals | Runs fraud analysis; reveals risk signals |
| request_additional_info | Requests missing documents |
| approve_claim | Terminal: accept the claim |
| reject_claim | Terminal: deny the claim |
| escalate_claim | Terminal: flag for human review |
| ignore | No-op (penalized) |

## Observation Space

| Field | Description |
|-------|-------------|
| claim | Claim type, amount, description, date |
| policy | Coverage, limits, exclusions, required documents |
| user_history | Previous claims, risk score, account age |
| documents | Document names and statuses |
| risk_signals | Fraud risk indicators with severity |
| underwriting_signals | Underwriting scores (revealed after analyze) |
| action_history | Actions taken so far |
| step_count | Current step number |
| reward | Reward from last action, strictly in (0,1) |
| done | Whether episode is complete |

## Reward Function

All rewards strictly in open interval (0,1) - never exactly 0.0 or 1.0. Dense rewards at every step.

Step components: decision_usefulness, information_gain, efficiency_penalty, consistency.
Terminal blend: Decision accuracy 38%, Fraud detection 28%, Reasoning 18%, Efficiency 16%.
Episode reward = 0.5 x avg step + 0.5 x terminal outcome.

## Tasks

### Easy: easy_claim_validation
Clean straightforward claims. Expected baseline score: 0.45-0.60

### Medium: medium_fraud_detection
Fraud signals, borderline limits, incomplete docs. Expected baseline score: 0.35-0.50

### Hard: hard_complex_multi_party
Conflicting signals, sophisticated fraud, multiple violations. Expected baseline score: 0.25-0.40

## Scenarios (18 total: 6 easy, 6 medium, 6 hard)

Easy: easy_001 (clean), easy_002 (policy_violation), easy_003 (health_simple), easy_004 (exclusion), easy_005 (docs_ok), easy_006 (low_amount)

Medium: medium_001 (borderline), medium_002 (fraud_suspicion), medium_003 (ambiguous_docs), medium_004 (staged_damage), medium_005 (approve_borderline), medium_006 (reject_under_limit)

Hard: hard_001 (conflicting_signals), hard_002 (sophisticated_fraud), hard_003 (adversarial_timing), hard_004 (silent_fraud), hard_005 (info_first), hard_006 (max_steps_pressure)

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /health | Health check |
| GET | /schema | Schemas |
| GET | /metadata | Metadata |
| GET | /scenarios | List scenarios |
| POST | /reset | Start episode |
| POST | /step | Take action |
| GET | /state | Current state |
| POST | /mcp | MCP endpoint |

## Running Inference

Set: API_BASE_URL, MODEL_NAME, HF_TOKEN, ENV_BASE_URL then run: python inference.py

Output format:
[START] task=easy_claim_validation env=insurance-claim-validation model=Qwen/Qwen2.5-72B-Instruct
[STEP] step=1 action=... reward=0.31 done=false error=null
[END] success=true steps=4 score=0.52 rewards=0.31,0.38,0.40,0.52

## License

BSD-3-Clause

## Acknowledgements

Built on OpenEnv by Meta PyTorch and Hugging Face.