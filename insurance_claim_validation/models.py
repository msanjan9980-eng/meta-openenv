# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""OpenEnv Action / Observation types for the insurance claim validation environment."""

from __future__ import annotations

from typing import Any, Dict, List, Literal

from openenv.core.env_server.types import Action, Observation
from pydantic import Field

from insurance_claim_validation.environment.schemas import (
    ClaimDetails,
    Document,
    PolicyInfo,
    ReasoningOutput,
    RiskSignal,
    UserHistory,
)


class ClaimAction(Action):
    """Discrete workflow action plus structured reasoning."""

    action: Literal[
        "analyze_claim",
        "detect_fraud_signals",
        "approve_claim",
        "reject_claim",
        "escalate_claim",
        "request_additional_info",
        "ignore",
    ]
    reasoning: ReasoningOutput
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ClaimObservation(Observation):
    """Rich observation; use ``revealed_facets`` to interpret partial views."""

    claim: ClaimDetails
    policy: PolicyInfo
    user_history: UserHistory
    documents: Dict[str, Document]
    risk_signals: List[RiskSignal] = Field(default_factory=list)
    derived_signals: Dict[str, Any] = Field(default_factory=dict)
    policy_violations: List[str] = Field(default_factory=list)
    underwriting_signals: Dict[str, float] = Field(default_factory=dict)
    step_count: int = 0
    action_history: List[str] = Field(default_factory=list)
    partial_observation: bool = True
    revealed_facets: List[str] = Field(default_factory=list)
