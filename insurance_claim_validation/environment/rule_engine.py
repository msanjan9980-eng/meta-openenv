# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Policy logic for grading (internal) and indirect underwriting signals (agent-facing)."""

from __future__ import annotations

from typing import Any, Dict, List

from insurance_claim_validation.models import ClaimObservation


class PolicyRuleEngine:
    def _check_policy_violations(self, obs: ClaimObservation) -> List[str]:
        violations: List[str] = []
        ct = obs.claim.claim_type.value
        limit = obs.policy.coverage_limits.get(ct, 0)
        if obs.claim.amount > limit:
            violations.append(
                f"Claim amount ${obs.claim.amount:.0f} exceeds coverage limit ${limit:.0f}"
            )
        days_since = (obs.claim.incident_date - obs.policy.created_at).days
        if days_since < obs.policy.waiting_period_days:
            violations.append("Incident occurred during waiting period")
        desc = obs.claim.description.lower()
        for exclusion in obs.policy.excluded_conditions:
            if exclusion.lower() in desc:
                violations.append(f"Excluded condition referenced: {exclusion}")
        if not obs.policy.active:
            violations.append("Policy is not active")
        return violations

    def evaluate(self, obs: ClaimObservation) -> Dict[str, Any]:
        return {
            "policy_violations": self._check_policy_violations(obs),
        }

    def underwriting_signal_scores(self, obs: ClaimObservation, rng) -> Dict[str, float]:
        """
        Indirect, bounded scores for the agent — no verbatim rule text or labels.
        Values are jittered so identical states are not perfectly repeatable.
        """
        ct = obs.claim.claim_type.value
        limit = obs.policy.coverage_limits.get(ct, 0) or 1e-6
        limit_stress = max(
            0.0, min(1.0, (obs.claim.amount - limit) / limit)
        )
        days_since = (obs.claim.incident_date - obs.policy.created_at).days
        wait = obs.policy.waiting_period_days
        waiting_stress = max(0.0, min(1.0, (wait - days_since) / max(1, wait)))

        desc = obs.claim.description.lower()
        excl_match = 0.0
        for exclusion in obs.policy.excluded_conditions:
            if exclusion.lower() in desc:
                excl_match = max(excl_match, 0.55)

        inactive = 0.0 if obs.policy.active else 0.95

        scores = {
            "limit_stress": float(
                max(0.04, min(0.96, limit_stress * rng.uniform(0.92, 1.08)))
            ),
            "waiting_period_stress": float(
                max(0.04, min(0.96, waiting_stress * rng.uniform(0.9, 1.1)))
            ),
            "exclusion_keyword_overlap": float(
                max(0.04, min(0.96, excl_match * rng.uniform(0.88, 1.05)))
            ),
            "policy_active_confidence": float(
                max(0.04, min(0.96, (1.0 - inactive) * rng.uniform(0.95, 1.02)))
            ),
        }
        return scores
