# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Deterministic policy checks used for observations and grading."""

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
