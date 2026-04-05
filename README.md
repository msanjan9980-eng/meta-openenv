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
3. Make decisions - approve, reject, escalate, or request more info
4. Reason about policy rules, user history, and document completeness

## Actions Available

- analyze_claim: Examine claim details more closely
- detect_fraud_signals: Run fraud detection analysis
- approve_claim: Accept the claim as valid
- reject_claim: Deny the claim
- escalate_claim: Flag for manual human review
- request_additional_info: Ask for missing documents
- ignore: Skip (penalized)

## Reward Structure

- Decision Accuracy: 40%
- Fraud Detection Quality: 30%
- Reasoning Quality: 20%
- Action Efficiency: 10%

Reward Range: 0.0 to 1.0

## Scenarios

17 scenarios across 3 difficulty levels:

Easy (5 scenarios):
- Clean auto claim
- Policy limit violation
- Clean health claim
- Missing documents
- Excluded condition

Medium (5 scenarios):
- Borderline health claim at limit
- Fraud suspicion with high frequency user
- Claim during waiting period
- New user with high value first claim
- Rejected documents

Hard (7 scenarios):
- Conflicting signals
- Sophisticated fraud with perfect docs
- Life insurance with suspicious timing
- Multiple simultaneous violations
- Legitimate high value claim
- Identity fraud
- Inactive policy claim

## API Endpoints

- GET  /          Environment info
- GET  /health    Health check
- GET  /schema    Action and observation schemas
- GET  /scenarios List all scenarios
- GET  /metrics   Episode metrics
- POST /reset     Reset environment
- POST /step      Take a step
- GET  /state     Current state
- WS   /ws/{id}   WebSocket connection

## Testing the API

Reset:
curl -X POST https://sanjan-m-insurance-claim-validation.hf.space/reset -H "Content-Type: application/json" -d "{}"

Health check:
curl https://sanjan-m-insurance-claim-validation.hf.space/health

Scenarios:
curl https://sanjan-m-insurance-claim-validation.hf.space/scenarios

## Architecture

environment/core.py - Main environment logic
environment/schemas.py - Data models
environment/rule_engine.py - Policy validation and fraud detection
environment/scenarios.py - 17 claim scenarios
environment/grader.py - Episode grading
inference/baseline_agent.py - LLM baseline agent
inference/evaluate.py - Evaluation script
server/app.py - FastAPI server
inference.py - Main inference script
openenv.yaml - Environment manifest

## License
BSD-3-Clause

## Acknowledgements
Built on OpenEnv by Meta PyTorch and Hugging Face.