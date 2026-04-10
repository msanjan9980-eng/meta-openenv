# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Controlled randomness per episode: noisy signals, not label leakage."""

from __future__ import annotations

import copy
from typing import Any, Dict, List

def perturb_scenario_for_episode(scenario: Dict[str, Any], rng) -> Dict[str, Any]:
    """
    Deep-copy scenario and add observation-level variability.

    Ground-truth labels are **not** changed — grading stays consistent with the template.
    """
    s = copy.deepcopy(scenario)

    # Jitter user risk score (measurement noise)
    u = s["user"]
    u["risk_score"] = float(
        max(0.06, min(0.94, u["risk_score"] + rng.uniform(-0.07, 0.07)))
    )

    # Risk signals: jitter severities, occasionally inject benign noise
    signals: List[Any] = list(s.get("risk_signals") or [])
    for item in signals:
        if isinstance(item, dict) and "severity" in item:
            item["severity"] = float(
                max(0.06, min(0.94, item["severity"] + rng.uniform(-0.09, 0.09)))
            )
        elif isinstance(item, RiskSignal):
            v = float(item.severity) + rng.uniform(-0.09, 0.09)
            item.severity = max(0.06, min(0.94, v))

    if rng.random() < 0.38:
        signals.append(
            {
                "signal_type": "telemetry_noise",
                "description": "Unverified auxiliary feed (latency / partial match)",
                "severity": rng.uniform(0.08, 0.42),
            }
        )

    s["risk_signals"] = signals

    return s
