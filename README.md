# Insurance Claim Validation Environment

An OpenEnv-compatible RL environment for training AI agents to validate insurance claims and detect fraud.

Built for the Meta PyTorch OpenEnv Hackathon 2026.

## Live Demo
- HF Space: https://huggingface.co/spaces/Sanjan-M/insurance-claim-validation
- API Docs: https://sanjan-m-insurance-claim-validation.hf.space/docs
- GitHub: https://github.com/msanjan9980-eng/meta-openenv

## What This Environment Does

This environment simulates a real-world insurance claim validation system where an AI agent must:
1. Analyze incoming insurance claims
2. Detect fraud patterns and suspicious behavior
3. Make decisions â€” approve, reject, escalate, or request more info
4. Reason about policy rules, user history, and document completeness

## Actions Available

| Action | Description |
|--------|-------------|
| analyze_claim | Examine claim details more closely |
| detect_fraud_signals | Run fraud detection analysis |
| approve_claim | Accept the claim as valid |
| reject_claim | Deny the claim |
| escalate_claim | Flag for manual human review |
| request_additional_info | Ask for missing documents |
| ignore | Skip (penalized) |

## Reward Structure

| Component | Weight | Description |
|-----------|--------|-------------|
| Decision Accuracy | 40% | Correct final action vs ground truth |
| Fraud Detection | 30% | Correctly identifying fraud |
| Reasoning Quality | 20% | Accurate reasoning about policy factors |
| Action Efficiency | 10% | Fewer steps = higher reward |

Reward Range: 0.0 to 1.0

## Scenarios

17 scenarios across 3 difficulty levels:

### Easy (5 scenarios)
- Clean auto claim
- Policy limit violation
- Clean health claim
- Missing documents
- Excluded condition

### Medium (5 scenarios)
- Borderline health claim at limit
- Fraud suspicion with high frequency user
- Claim during waiting period
- New user with high value first claim
- Rejected documents

### Hard (7 scenarios)
- Conflicting signals
- Sophisticated fraud with perfect docs
- Life insurance with suspicious timing
- Multiple simultaneous violations
- Legitimate high value claim
- Identity fraud
- Inactive policy claim

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | / | Environment info |
| GET | /health | Health check |
| GET | /schema | Action and observation schemas |
| GET | /scenarios | List all scenarios |
| GET | /metrics | Episode metrics |
| POST | /reset | Reset environment |
| POST | /step | Take a step |
| GET | /state | Current state |
| WS | /ws/{session_id} | WebSocket connection |

## Testing the API

Reset the environment:
curl -X POST https://sanjan-m-insurance-claim-validation.hf.space/reset -H "Content-Type: application/json" -d "{}"

Health check:
curl https://sanjan-m-insurance-claim-validation.hf.space/health

View all scenarios:
curl https://sanjan-m-insurance-claim-validation.hf.space/scenarios

## Architecture

environment/core.py â€” Main environment logic
environment/schemas.py â€” Data models
environment/rule_engine.py â€” Policy validation and fraud detection
environment/scenarios.py â€” 17 claim scenarios
environment/grader.py â€” Episode grading
inference/baseline_agent.py â€” LLM baseline agent
inference/evaluate.py â€” Evaluation script
server/app.py â€” FastAPI server
inference.py â€” Main inference script
openenv.yaml â€” Environment manifest

## License
BSD-3-Clause

## Acknowledgements
Built on OpenEnv by Meta PyTorch and Hugging Face.
