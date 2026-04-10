# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""
Validator-safe rewards: internal canonical scores in [0, 1], then mapped to a strict
open interval (epsilon, 1 - epsilon). No literal 0.0 / 1.0 assignments on returned rewards.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from insurance_claim_validation.environment.schemas import DocumentStatus, ReasoningOutput
from insurance_claim_validation.models import ClaimAction

# Open interval (0, 1) — never return exactly 0 or 1 after mapping.
REWARD_EPS: float = 1e-3


def reward_epsilon() -> float:
    return REWARD_EPS


def squeeze_to_open_interval(x: float) -> float:
    """
    Map canonical score in [0, 1] strictly inside (REWARD_EPS, 1 - REWARD_EPS).

    Endpoints of the canonical range never map to the boundary — avoids exact
    0.0 / 1.0 floats after rounding for typical validators.
    """
    x = max(0.0, min(1.0, float(x)))
    lo = REWARD_EPS
    hi = 1.0 - REWARD_EPS
    span = hi - lo
    margin = span * 1e-6
    return lo + margin + (span - 2.0 * margin) * x


def _soft_decision_quality(terminal_action: str, correct: str) -> float:
    """Partial credit; values stay in (0, 1) before squeeze."""
    if terminal_action == correct:
        return 0.94
    # Same "family" (all terminal decisions)
    escalate = "escalate_claim"
    if terminal_action == escalate or correct == escalate:
        return 0.28
    if {terminal_action, correct} == {"approve_claim", "reject_claim"}:
        return 0.22
    return 0.14


def _soft_fraud_quality(actual_fraud: bool, flagged: bool) -> float:
    if actual_fraud and flagged:
        return 0.93
    if not actual_fraud and not flagged:
        return 0.92
    if actual_fraud and not flagged:
        return 0.18
    return 0.36  # false positive


def _score_reasoning_soft(r: ReasoningOutput, gt: Dict[str, Any]) -> float:
    checks = [
        (r.policy_violation, gt.get("has_policy_violation", False)),
        (r.claim_amount_valid, gt.get("amount_valid", True)),
        (r.user_risk_high, gt.get("user_high_risk", False)),
        (r.documents_complete, gt.get("docs_complete", False)),
    ]
    matches = sum(1 for a, b in checks if a == b)
    # Smooth partial credit: baseline + fraction (never exactly 0 or 1)
    return 0.12 + 0.86 * (matches / len(checks))


def _efficiency_soft(total_steps: int, max_steps: int) -> float:
    if max_steps <= 0:
        return 0.5
    # Normalized path length; prefer neither extremely short nor maxed-out episodes.
    t = total_steps / max_steps
    # Peak around mid-range: avoids bias to only very short episodes.
    return 0.25 + 0.7 * (1.0 - abs(t - 0.55) / 0.55)


def _sequence_readiness_factor(
    actions: List[ClaimAction],
    ground_truth: Dict[str, Any],
) -> float:
    """
    Penalize premature terminal decisions; reward structured exploration.
    Returns a multiplier in (0, 1] applied to the *canonical* final composite.
    """
    terminal_actions = ("approve_claim", "reject_claim", "escalate_claim")
    term_idx: Optional[int] = None
    for i, a in enumerate(actions):
        if a.action in terminal_actions:
            term_idx = i
            break
    if term_idx is None:
        return 0.42

    prior = actions[:term_idx]
    has_analyze = any(a.action == "analyze_claim" for a in prior)
    has_detect = any(a.action == "detect_fraud_signals" for a in prior)
    has_request = any(a.action == "request_additional_info" for a in prior)
    need = ground_truth.get("correct_action")

    # Ideal prep depends on label — still soft, not binary gates.
    prep_score = 0.18
    if has_analyze:
        prep_score += 0.28
    if has_detect:
        prep_score += 0.27
    if need == "request_additional_info" and has_request:
        prep_score += 0.22
    elif need != "request_additional_info" and has_request:
        prep_score += 0.08

    # Premature terminal (step index 0 = first action)
    step_number = term_idx + 1
    if step_number <= 1:
        prep_score *= 0.35
    elif step_number == 2 and not has_analyze:
        prep_score *= 0.55
    elif step_number <= 2 and not (has_analyze and has_detect):
        prep_score *= 0.72

    return max(0.08, min(0.99, prep_score))


def compute_step_reward(
    action: ClaimAction,
    prev_action: Optional[str],
    ground_truth: Dict[str, Any],
    docs_complete: bool,
) -> Tuple[float, Dict[str, float]]:
    """
    Returns (canonical_step_score, component dict). Caller applies squeeze for API reward.
    Canonical scores are built from soft partials — no hard 0/1.
    """
    name = action.action
    need = ground_truth["correct_action"]

    usefulness = 0.11
    if name in ("analyze_claim", "detect_fraud_signals", "request_additional_info"):
        if need == "request_additional_info" and not docs_complete and name == "request_additional_info":
            usefulness = 0.29
        elif need in ("approve_claim", "reject_claim") and name in (
            "analyze_claim",
            "detect_fraud_signals",
        ):
            usefulness = 0.26
        elif need == "escalate_claim" and name in ("analyze_claim", "detect_fraud_signals"):
            usefulness = 0.27
        else:
            usefulness = 0.15
    elif name in ("approve_claim", "reject_claim", "escalate_claim"):
        usefulness = 0.19 + 0.12 * _soft_decision_quality(name, need)
    elif name == "ignore":
        usefulness = 0.06

    info_gain = 0.11
    if name == "analyze_claim":
        info_gain = 0.21
    elif name == "detect_fraud_signals":
        info_gain = 0.23
    elif name == "request_additional_info" and not docs_complete:
        info_gain = 0.19
    elif name in ("approve_claim", "reject_claim", "escalate_claim"):
        info_gain = 0.09

    efficiency_penalty = -0.048
    consistency = 0.0
    if prev_action is not None and prev_action == name:
        consistency = -0.095
    elif prev_action is not None and prev_action != name and name != "ignore":
        consistency = 0.048

    raw = usefulness + info_gain + efficiency_penalty + consistency
    raw = max(0.02, min(0.98, raw))
    components = {
        "decision_usefulness": usefulness,
        "information_gain": info_gain,
        "efficiency_penalty": efficiency_penalty,
        "consistency": consistency,
        "canonical_raw": raw,
    }
    return raw, components


def compute_final_outcome_reward(
    actions: List[ClaimAction],
    ground_truth: Dict[str, Any],
    total_steps: int,
    max_steps: int,
) -> Tuple[float, Dict[str, float]]:
    """
    Single terminal evaluation: weighted soft components × sequence readiness.
    Returns canonical composite in (0, 1) before squeeze.
    """
    terminal_actions = ("approve_claim", "reject_claim", "escalate_claim")
    terminal: Optional[ClaimAction] = None
    for a in reversed(actions):
        if a.action in terminal_actions:
            terminal = a
            break
    if terminal is None and actions:
        terminal = actions[-1]
    if terminal is None:
        low = 0.14
        return low, {
            "decision": 0.05,
            "fraud_detection": 0.05,
            "reasoning": 0.02,
            "efficiency": 0.02,
            "sequence_readiness": 0.0,
            "canonical_composite": low,
        }

    r = terminal.reasoning
    correct = ground_truth["correct_action"]
    d = _soft_decision_quality(terminal.action, correct)
    fraud_actual = bool(ground_truth["fraud_label"])
    fraud_flagged = len(r.fraud_indicators) > 0
    f = _soft_fraud_quality(fraud_actual, fraud_flagged)
    rs = _score_reasoning_soft(r, ground_truth)
    eff = _efficiency_soft(total_steps, max_steps)

    seq = _sequence_readiness_factor(actions, ground_truth)

    # Weighted blend (weights sum to 1); then modulate by sequence (never multiply to 0).
    composite = (
        0.38 * d + 0.28 * f + 0.18 * rs + 0.16 * eff
    ) * max(0.12, seq)

    composite = max(0.05, min(0.97, composite))

    breakdown = {
        "decision": 0.38 * d,
        "fraud_detection": 0.28 * f,
        "reasoning": 0.18 * rs,
        "efficiency": 0.16 * eff,
        "sequence_readiness": seq,
        "canonical_composite": composite,
    }
    return composite, breakdown


def aggregate_episode_reward(
    step_canonical_values: List[float], final_canonical: float
) -> float:
    """Combine average step quality with final outcome; equal weighting of both parts."""
    if not step_canonical_values:
        return max(0.06, min(0.96, 0.55 * final_canonical + 0.45 * 0.35))
    avg_step = sum(step_canonical_values) / len(step_canonical_values)
    combined = 0.5 * avg_step + 0.5 * final_canonical
    return max(0.05, min(0.98, combined))


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
