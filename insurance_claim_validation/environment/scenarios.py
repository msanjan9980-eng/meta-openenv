# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""18 curated claim scenarios (easy / medium / hard) with ground truth."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from insurance_claim_validation.environment.schemas import (
    ClaimType,
    DocumentStatus,
    RiskSignal,
)


def _dt(days_ago: int) -> datetime:
    return datetime.now() - timedelta(days=days_ago)


def _build_scenarios() -> List[Dict[str, Any]]:
    s: List[Dict[str, Any]] = []

    # --- Easy (6) ---
    s.append(
        {
            "id": "easy_001",
            "difficulty": "easy",
            "tag": "clean",
            "description": "Valid auto claim within limits, complete docs",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 2500,
                "description": "Rear-ended at traffic light, moderate damage to bumper",
                "incident_date": _dt(3),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 5000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["police_report", "photos", "estimate"],
            },
            "user": {
                "total_claims": 1,
                "total_payout": 1800,
                "previous_claims": [{"date": _dt(365), "amount": 1800}],
                "account_age_days": 730,
                "claim_frequency": 0.5,
                "flagged_previous": False,
                "risk_score": 0.2,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "easy_002",
            "difficulty": "easy",
            "tag": "policy_violation",
            "description": "Home claim exceeds coverage",
            "claim": {
                "claim_type": ClaimType.HOME,
                "amount": 15000,
                "description": "Water damage from burst pipe, flooding basement",
                "incident_date": _dt(5),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"home": 10000},
                "deductibles": {"home": 1000},
                "waiting_period_days": 0,
                "excluded_conditions": ["flood"],
                "required_documents": ["photos", "contractor_estimate", "plumber_report"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 180,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.1,
            },
            "documents": {
                "photos": DocumentStatus.VERIFIED,
                "contractor_estimate": DocumentStatus.VERIFIED,
                "plumber_report": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "reject_claim",
                "fraud_label": False,
                "has_policy_violation": True,
                "amount_valid": False,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "easy_003",
            "difficulty": "easy",
            "tag": "health_simple",
            "description": "Routine health claim, all docs verified",
            "claim": {
                "claim_type": ClaimType.HEALTH,
                "amount": 1200,
                "description": "Doctor visit and lab tests for annual checkup",
                "incident_date": _dt(10),
                "severity": "low",
            },
            "policy": {
                "coverage_limits": {"health": 5000},
                "deductibles": {"health": 250},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["medical_report", "hospital_bill"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 400,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.15,
            },
            "documents": {
                "medical_report": DocumentStatus.VERIFIED,
                "hospital_bill": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "easy_004",
            "difficulty": "easy",
            "tag": "exclusion",
            "description": "Auto claim description mentions excluded racing use",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 3000,
                "description": "Damage while participating in an organized racing event on track",
                "incident_date": _dt(2),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 10000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": ["racing"],
                "required_documents": ["police_report", "photos"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 600,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.2,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "reject_claim",
                "fraud_label": False,
                "has_policy_violation": True,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "easy_005",
            "difficulty": "easy",
            "tag": "docs_ok",
            "description": "Life policy small claim",
            "claim": {
                "claim_type": ClaimType.LIFE,
                "amount": 5000,
                "description": "Accidental death benefit paperwork submitted with coroner report",
                "incident_date": _dt(30),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"life": 100000},
                "deductibles": {"life": 0},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["death_certificate", "police_report"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 2000,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.1,
            },
            "documents": {
                "death_certificate": DocumentStatus.VERIFIED,
                "police_report": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "easy_006",
            "difficulty": "easy",
            "tag": "low_amount",
            "description": "Minor auto scratch — clearly valid",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 400,
                "description": "Parking lot scratch on driver door paint",
                "incident_date": _dt(1),
                "severity": "low",
            },
            "policy": {
                "coverage_limits": {"auto": 5000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["photos", "estimate"],
            },
            "user": {
                "total_claims": 2,
                "total_payout": 900,
                "previous_claims": [],
                "account_age_days": 900,
                "claim_frequency": 0.8,
                "flagged_previous": False,
                "risk_score": 0.25,
            },
            "documents": {
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )

    # --- Medium (6) ---
    s.append(
        {
            "id": "medium_001",
            "difficulty": "medium",
            "tag": "borderline",
            "description": "Health claim at limit with missing prescription",
            "claim": {
                "claim_type": ClaimType.HEALTH,
                "amount": 5000,
                "description": "Emergency room visit for severe allergic reaction",
                "incident_date": _dt(2),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"health": 5000},
                "deductibles": {"health": 250},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["medical_report", "hospital_bill", "prescription"],
            },
            "user": {
                "total_claims": 2,
                "total_payout": 3200,
                "previous_claims": [
                    {"date": _dt(200), "amount": 1500},
                    {"date": _dt(400), "amount": 1700},
                ],
                "account_age_days": 500,
                "claim_frequency": 1.46,
                "flagged_previous": False,
                "risk_score": 0.4,
            },
            "documents": {
                "medical_report": DocumentStatus.UPLOADED,
                "hospital_bill": DocumentStatus.PENDING,
                "prescription": DocumentStatus.MISSING,
            },
            "risk_signals": [
                {
                    "signal_type": "noise",
                    "description": "Slight mismatch on visit date (data entry)",
                    "severity": 0.2,
                }
            ],
            "ground_truth": {
                "correct_action": "request_additional_info",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": False,
            },
        }
    )
    s.append(
        {
            "id": "medium_002",
            "difficulty": "medium",
            "tag": "fraud_suspicion",
            "description": "Suspicious frequency, escalate",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 4800,
                "description": "Hit and run, car damaged",
                "incident_date": _dt(1),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 5000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["police_report", "photos", "estimate"],
            },
            "user": {
                "total_claims": 3,
                "total_payout": 12500,
                "previous_claims": [
                    {"date": _dt(30), "amount": 4500},
                    {"date": _dt(90), "amount": 3800},
                    {"date": _dt(150), "amount": 4200},
                ],
                "account_age_days": 200,
                "claim_frequency": 5.475,
                "flagged_previous": True,
                "risk_score": 0.7,
            },
            "documents": {
                "police_report": DocumentStatus.UPLOADED,
                "photos": DocumentStatus.UPLOADED,
                "estimate": DocumentStatus.PENDING,
            },
            "risk_signals": [
                {
                    "signal_type": "frequency",
                    "description": "Multiple claims in 6 months",
                    "severity": 0.55,
                }
            ],
            "ground_truth": {
                "correct_action": "escalate_claim",
                "fraud_label": True,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": True,
                "docs_complete": False,
            },
        }
    )
    s.append(
        {
            "id": "medium_003",
            "difficulty": "medium",
            "tag": "ambiguous_docs",
            "description": "Home claim — one doc pending",
            "claim": {
                "claim_type": ClaimType.HOME,
                "amount": 7000,
                "description": "Hail damage to roof and siding",
                "incident_date": _dt(14),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"home": 20000},
                "deductibles": {"home": 1500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["photos", "contractor_estimate", "weather_report"],
            },
            "user": {
                "total_claims": 1,
                "total_payout": 2000,
                "previous_claims": [{"date": _dt(400), "amount": 2000}],
                "account_age_days": 800,
                "claim_frequency": 0.45,
                "flagged_previous": False,
                "risk_score": 0.35,
            },
            "documents": {
                "photos": DocumentStatus.VERIFIED,
                "contractor_estimate": DocumentStatus.VERIFIED,
                "weather_report": DocumentStatus.PENDING,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "request_additional_info",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": False,
            },
        }
    )
    s.append(
        {
            "id": "medium_004",
            "difficulty": "medium",
            "tag": "staged_damage",
            "description": "Possible staged collision — escalate for SIU",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 4200,
                "description": "Rear collision with conflicting witness statements",
                "incident_date": _dt(4),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 8000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["police_report", "photos", "estimate"],
            },
            "user": {
                "total_claims": 1,
                "total_payout": 3000,
                "previous_claims": [],
                "account_age_days": 120,
                "claim_frequency": 3.0,
                "flagged_previous": False,
                "risk_score": 0.55,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [
                {
                    "signal_type": "witness_conflict",
                    "description": "Witness statements disagree on lane of travel",
                    "severity": 0.6,
                }
            ],
            "ground_truth": {
                "correct_action": "escalate_claim",
                "fraud_label": True,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "medium_005",
            "difficulty": "medium",
            "tag": "approve_borderline",
            "description": "Valid but high-risk user — still approvable",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 3500,
                "description": "Side swipe in merge lane, body shop estimate attached",
                "incident_date": _dt(6),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 6000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["police_report", "photos", "estimate"],
            },
            "user": {
                "total_claims": 4,
                "total_payout": 14000,
                "previous_claims": [],
                "account_age_days": 400,
                "claim_frequency": 3.6,
                "flagged_previous": True,
                "risk_score": 0.72,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": True,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "medium_006",
            "difficulty": "medium",
            "tag": "reject_under_limit",
            "description": "Clear policy breach — amount OK but excluded peril",
            "claim": {
                "claim_type": ClaimType.HOME,
                "amount": 2000,
                "description": "Mold damage in bathroom from long-term humidity",
                "incident_date": _dt(20),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"home": 15000},
                "deductibles": {"home": 1000},
                "waiting_period_days": 0,
                "excluded_conditions": ["mold"],
                "required_documents": ["photos", "inspection_report"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 300,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.2,
            },
            "documents": {
                "photos": DocumentStatus.VERIFIED,
                "inspection_report": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "reject_claim",
                "fraud_label": False,
                "has_policy_violation": True,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )

    # --- Hard (6) ---
    s.append(
        {
            "id": "hard_001",
            "difficulty": "hard",
            "tag": "conflicting_signals",
            "description": "Electrical fire exclusion vs repeat claim",
            "claim": {
                "claim_type": ClaimType.HOME,
                "amount": 9500,
                "description": "Fire damage from electrical malfunction. Similar claim 6 months ago.",
                "incident_date": _dt(4),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"home": 10000},
                "deductibles": {"home": 1000},
                "waiting_period_days": 0,
                "excluded_conditions": ["electrical_fire"],
                "required_documents": [
                    "fire_report",
                    "photos",
                    "contractor_estimate",
                    "electrical_inspection",
                ],
            },
            "user": {
                "total_claims": 2,
                "total_payout": 8800,
                "previous_claims": [
                    {"date": _dt(180), "amount": 8800, "type": "electrical_fire"}
                ],
                "account_age_days": 365,
                "claim_frequency": 2.0,
                "flagged_previous": True,
                "risk_score": 0.6,
            },
            "documents": {
                "fire_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "contractor_estimate": DocumentStatus.UPLOADED,
                "electrical_inspection": DocumentStatus.MISSING,
            },
            "risk_signals": [
                {
                    "signal_type": "repeat_peril",
                    "description": "Prior electrical fire claim within 12 months",
                    "severity": 0.75,
                }
            ],
            "ground_truth": {
                "correct_action": "escalate_claim",
                "fraud_label": True,
                "has_policy_violation": True,
                "amount_valid": True,
                "user_high_risk": True,
                "docs_complete": False,
            },
        }
    )
    s.append(
        {
            "id": "hard_002",
            "difficulty": "hard",
            "tag": "sophisticated_fraud",
            "description": "Staged multi-vehicle — docs look perfect",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 4950,
                "description": "Multi-vehicle collision on highway, extensive damage, full documentation",
                "incident_date": _dt(10),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"auto": 5000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": [
                    "police_report",
                    "photos",
                    "estimate",
                    "witness_statements",
                ],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 25,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.1,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
                "witness_statements": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "reject_claim",
                "fraud_label": True,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": True,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "hard_003",
            "difficulty": "hard",
            "tag": "adversarial_timing",
            "description": "Same-day filing — fraud pattern but valid claim",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 2800,
                "description": "Glass damage from road debris on highway",
                "incident_date": _dt(0),
                "severity": "low",
            },
            "policy": {
                "coverage_limits": {"auto": 7000},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["photos", "estimate"],
            },
            "user": {
                "total_claims": 0,
                "total_payout": 0,
                "previous_claims": [],
                "account_age_days": 500,
                "claim_frequency": 0.0,
                "flagged_previous": False,
                "risk_score": 0.18,
            },
            "documents": {
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [
                {
                    "signal_type": "immediate_filing",
                    "description": "Claim filed same calendar day as incident",
                    "severity": 0.45,
                }
            ],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "hard_004",
            "difficulty": "hard",
            "tag": "silent_fraud",
            "description": "Low risk score but phantom provider",
            "claim": {
                "claim_type": ClaimType.HEALTH,
                "amount": 4500,
                "description": "Out-of-network surgery follow-up bills",
                "incident_date": _dt(7),
                "severity": "high",
            },
            "policy": {
                "coverage_limits": {"health": 8000},
                "deductibles": {"health": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["medical_report", "hospital_bill", "prescription"],
            },
            "user": {
                "total_claims": 1,
                "total_payout": 1000,
                "previous_claims": [],
                "account_age_days": 700,
                "claim_frequency": 0.5,
                "flagged_previous": False,
                "risk_score": 0.22,
            },
            "documents": {
                "medical_report": DocumentStatus.VERIFIED,
                "hospital_bill": DocumentStatus.VERIFIED,
                "prescription": DocumentStatus.VERIFIED,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "reject_claim",
                "fraud_label": True,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )
    s.append(
        {
            "id": "hard_005",
            "difficulty": "hard",
            "tag": "info_first",
            "description": "Needs info before any terminal decision",
            "claim": {
                "claim_type": ClaimType.HEALTH,
                "amount": 3200,
                "description": "Physical therapy after fall — billing incomplete",
                "incident_date": _dt(5),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"health": 6000},
                "deductibles": {"health": 300},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["medical_report", "hospital_bill", "referral"],
            },
            "user": {
                "total_claims": 2,
                "total_payout": 4100,
                "previous_claims": [],
                "account_age_days": 600,
                "claim_frequency": 1.2,
                "flagged_previous": False,
                "risk_score": 0.38,
            },
            "documents": {
                "medical_report": DocumentStatus.UPLOADED,
                "hospital_bill": DocumentStatus.MISSING,
                "referral": DocumentStatus.PENDING,
            },
            "risk_signals": [],
            "ground_truth": {
                "correct_action": "request_additional_info",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": False,
            },
        }
    )
    s.append(
        {
            "id": "hard_006",
            "difficulty": "hard",
            "tag": "max_steps_pressure",
            "description": "Borderline approve — policy ok, mild fraud noise",
            "claim": {
                "claim_type": ClaimType.AUTO,
                "amount": 5100,
                "description": "Parking garage scrape involving two vehicles",
                "incident_date": _dt(3),
                "severity": "medium",
            },
            "policy": {
                "coverage_limits": {"auto": 5500},
                "deductibles": {"auto": 500},
                "waiting_period_days": 0,
                "excluded_conditions": [],
                "required_documents": ["police_report", "photos", "estimate"],
            },
            "user": {
                "total_claims": 2,
                "total_payout": 8000,
                "previous_claims": [],
                "account_age_days": 500,
                "claim_frequency": 1.4,
                "flagged_previous": False,
                "risk_score": 0.48,
            },
            "documents": {
                "police_report": DocumentStatus.VERIFIED,
                "photos": DocumentStatus.VERIFIED,
                "estimate": DocumentStatus.VERIFIED,
            },
            "risk_signals": [
                {
                    "signal_type": "amount_near_limit",
                    "description": "Claim within 8% of annual limit",
                    "severity": 0.5,
                }
            ],
            "ground_truth": {
                "correct_action": "approve_claim",
                "fraud_label": False,
                "has_policy_violation": False,
                "amount_valid": True,
                "user_high_risk": False,
                "docs_complete": True,
            },
        }
    )

    return s


class ScenarioGenerator:
    def __init__(self) -> None:
        self.scenarios = _build_scenarios()

    def get_all_scenario_ids(self) -> List[str]:
        return [x["id"] for x in self.scenarios]

    def get_scenarios_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        return [x for x in self.scenarios if x["difficulty"] == difficulty]

    def get_scenario(
        self, scenario_id: Optional[str] = None, difficulty: Optional[str] = None
    ) -> Dict[str, Any]:
        import random

        if scenario_id:
            for s in self.scenarios:
                if s["id"] == scenario_id:
                    return s
        pool = self.scenarios
        if difficulty:
            pool = [x for x in self.scenarios if x["difficulty"] == difficulty]
        return random.choice(pool)
