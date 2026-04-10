# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Nested Pydantic models for claims, policies, and agent reasoning."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, Field


class ClaimType(str, Enum):
    AUTO = "auto"
    HOME = "home"
    HEALTH = "health"
    LIFE = "life"


class DocumentStatus(str, Enum):
    MISSING = "missing"
    PENDING = "pending"
    UPLOADED = "uploaded"
    VERIFIED = "verified"
    REJECTED = "rejected"


class RiskSignal(BaseModel):
    signal_type: str
    description: str
    severity: float = Field(ge=0.0, le=1.0)
    timestamp: datetime = Field(default_factory=datetime.now)


class ClaimDetails(BaseModel):
    claim_id: str = Field(default_factory=lambda: str(uuid4()))
    claim_type: ClaimType
    amount: float = Field(gt=0)
    description: str
    incident_date: datetime
    filing_date: datetime = Field(default_factory=datetime.now)
    location: Optional[str] = None
    severity: Literal["low", "medium", "high"] = "medium"


class UserHistory(BaseModel):
    user_id: str
    total_claims: int = 0
    total_payout: float = 0.0
    previous_claims: List[Dict[str, Any]] = Field(default_factory=list)
    account_age_days: int = Field(default=0)
    claim_frequency: float = Field(default=0.0)
    flagged_previous: bool = False
    risk_score: float = Field(default=0.0, ge=0.0, le=1.0)


class Document(BaseModel):
    doc_type: str
    status: DocumentStatus
    url: Optional[str] = None
    uploaded_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    notes: Optional[str] = None


class PolicyInfo(BaseModel):
    policy_id: str
    coverage_limits: Dict[str, float]
    deductibles: Dict[str, float]
    waiting_period_days: int = 0
    excluded_conditions: List[str] = Field(default_factory=list)
    required_documents: List[str] = Field(default_factory=list)
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.now)


class ReasoningOutput(BaseModel):
    """Structured rationale supplied with each action (used for grading)."""

    policy_violation: bool = False
    claim_amount_valid: bool = True
    user_risk_high: bool = False
    documents_complete: bool = False
    fraud_indicators: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    recommendation: Optional[str] = None

    model_config = {"extra": "forbid"}
