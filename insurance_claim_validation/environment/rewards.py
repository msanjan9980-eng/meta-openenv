# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""PRD reward: dense step rewards in [0,1] and terminal outcome mix."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from insurance_claim_validation.environment.schemas import DocumentStatus, ReasoningOutput
from insurance_claim_validation.models import ClaimAction


def _clip(x: float) -> float:
    return max(0.0, min(1.0, x))


def compute_step_reward(
    action: ClaimAction,
    prev_action: Optional[str],
    ground_truth: Dict[str, Any],
    docs_complete: bool,
) -> Tuple[float, Dict[str, float]]:
    """
    R_step ∈ [0,1] with components:
    - decision usefulness [0, 0.3]
    - information gain [0, 0.2]
    - efficiency penalty -0.05 per step
    - consistency bonus [-0.1, +0.1]
    """
    name = action.action

    # Decision usefulness (0–0.3): action is aligned with scenario needs
    usefulness = 0.0
    need = ground_truth["correct_action"]
    if name in ("analyze_claim", "detect_fraud_signals", "request_additional_info"):
        if need == "request_additional_info" and not docs_complete and name == "request_additional_info":
            usefulness = 0.3
        elif need in ("approve_claim", "reject_claim") and name in ("analyze_claim", "detect_fraud_signals"):
            usefulness = 0.25
        elif need == "escalate_claim" and name in ("analyze_claim", "detect_fraud_signals"):
            usefulness = 0.28
        else:
            usefulness = 0.12
    elif name in ("approve_claim", "reject_claim", "escalate_claim"):
        usefulness = 0.15 if name == need else 0.05
    elif name == "ignore":
        usefulness = 0.0
    else:
        usefulness = 0.1

    # Information gain (0–0.2)
    info_gain = 0.0
    if name == "analyze_claim":
        info_gain = 0.18
    elif name == "detect_fraud_signals":
        info_gain = 0.2
    elif name == "request_additional_info" and not docs_complete:
        info_gain = 0.16
    elif name in ("approve_claim", "reject_claim", "escalate_claim"):
        info_gain = 0.05

    # Efficiency penalty: −0.05 per step (as additive component)
    efficiency_penalty = -0.05

    # Consistency bonus [−0.1, +0.1]
    consistency = 0.0
    if prev_action is not None and prev_action == name:
        consistency = -0.1
    elif prev_action is not None and prev_action != name and name != "ignore":
        consistency = 0.05

    raw = usefulness + info_gain + efficiency_penalty + consistency
    reward = _clip(raw)
    components = {
        "decision_usefulness": usefulness,
        "information_gain": info_gain,
        "efficiency_penalty": efficiency_penalty,
        "consistency": consistency,
        "raw_before_clip": raw,
    }
    return reward, components


def compute_final_outcome_reward(
    actions: List[ClaimAction],
    ground_truth: Dict[str, Any],
    total_steps: int,
    max_steps: int,
) -> Tuple[float, Dict[str, float]]:
    """
    R_final_outcome ∈ [0,1] with weights:
    decision 0.4, fraud 0.3, reasoning 0.2, efficiency 0.1
    """
    terminal_actions = ("approve_claim", "reject_claim", "escalate_claim")
    terminal: Optional[ClaimAction] = None
    for a in reversed(actions):
        if a.action in terminal_actions:
            terminal = a
            break
    if terminal is None:
        terminal = actions[-1] if actions else None
    if terminal is None:
        return 0.0, {
            "decision": 0.0,
            "fraud_detection": 0.0,
            "reasoning": 0.0,
            "efficiency": 0.0,
        }

    r = terminal.reasoning
    correct = ground_truth["correct_action"]
    decision_score = 1.0 if terminal.action == correct else 0.0

    fraud_actual = bool(ground_truth["fraud_label"])
    fraud_flagged = len(r.fraud_indicators) > 0
    if fraud_actual and fraud_flagged:
        fraud_score = 1.0
    elif not fraud_actual and not fraud_flagged:
        fraud_score = 1.0
    elif fraud_actual and not fraud_flagged:
        fraud_score = 0.0
    else:
        fraud_score = 0.5

    reasoning_score = _score_reasoning(r, ground_truth)
    efficiency_score = max(0.0, 1.0 - (total_steps / max_steps))

    final = _clip(
        0.4 * decision_score
        + 0.3 * fraud_score
        + 0.2 * reasoning_score
        + 0.1 * efficiency_score
    )
    breakdown = {
        "decision": 0.4 * decision_score,
        "fraud_detection": 0.3 * fraud_score,
        "reasoning": 0.2 * reasoning_score,
        "efficiency": 0.1 * efficiency_score,
    }
    return final, breakdown


def _score_reasoning(r: ReasoningOutput, gt: Dict[str, Any]) -> float:
    checks = [
        r.policy_violation == gt.get("has_policy_violation", False),
        r.claim_amount_valid == gt.get("amount_valid", True),
        r.user_risk_high == gt.get("user_high_risk", False),
        r.documents_complete == gt.get("docs_complete", False),
    ]
    return sum(1 for c in checks if c) / len(checks)


def aggregate_episode_reward(
    step_rewards: List[float], final_outcome: float
) -> float:
    if not step_rewards:
        return _clip(final_outcome)
    avg_step = sum(step_rewards) / len(step_rewards)
    return _clip(0.5 * avg_step + 0.5 * final_outcome)


def docs_complete_from_documents(
    documents: Dict[str, Any], required: List[str]
) -> bool:
    for r in required:
        d = documents.get(r)
        if d is None:
            return False
        if isinstance(d, dict):
            st = d.get("status")
            if st in ("missing", "pending"):
                return False
        elif d.status in (DocumentStatus.MISSING, DocumentStatus.PENDING):
            return False
    return True
