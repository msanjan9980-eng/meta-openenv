from typing import Dict, Any, List
from datetime import datetime, timedelta
from .schemas import (
    ClaimType, DocumentStatus, ClaimDetails, PolicyInfo,
    UserHistory, Document, RiskSignal
)

class ScenarioGenerator:
    """Generate realistic claim scenarios with ground truth"""

    def __init__(self):
        self.scenarios = self._build_scenarios()

    def _build_scenarios(self) -> List[Dict[str, Any]]:
        scenarios = []

        # ==================== EASY SCENARIOS ====================
        scenarios.extend([
            {
                "id": "easy_001",
                "difficulty": "easy",
                "tag": "clean_auto",
                "description": "Valid auto claim within limits, complete docs",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 2500,
                    "description": "Rear-ended at traffic light, moderate damage to bumper and trunk",
                    "incident_date": datetime.now() - timedelta(days=3),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["police_report", "photos", "estimate"]
                },
                "user": {
                    "total_claims": 1,
                    "total_payout": 1800,
                    "previous_claims": [{"date": datetime.now() - timedelta(days=365), "amount": 1800}],
                    "account_age_days": 730,
                    "claim_frequency": 0.5,
                    "flagged_previous": False,
                    "risk_score": 0.2
                },
                "documents": {
                    "police_report": DocumentStatus.VERIFIED,
                    "photos": DocumentStatus.VERIFIED,
                    "estimate": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "approve_claim",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
            {
                "id": "easy_002",
                "difficulty": "easy",
                "tag": "policy_violation_limit",
                "description": "Claim exceeding coverage limits",
                "claim": {
                    "claim_type": ClaimType.HOME,
                    "amount": 15000,
                    "description": "Water damage from burst pipe, flooding basement and living room",
                    "incident_date": datetime.now() - timedelta(days=5),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"home": 10000},
                    "deductibles": {"home": 1000},
                    "waiting_period_days": 0,
                    "excluded_conditions": ["flood"],
                    "required_documents": ["photos", "contractor_estimate", "plumber_report"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 180,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.1
                },
                "documents": {
                    "photos": DocumentStatus.VERIFIED,
                    "contractor_estimate": DocumentStatus.VERIFIED,
                    "plumber_report": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": False,
                    "has_policy_violation": True,
                    "amount_valid": False,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
            {
                "id": "easy_003",
                "difficulty": "easy",
                "tag": "clean_health",
                "description": "Valid health claim with complete documentation",
                "claim": {
                    "claim_type": ClaimType.HEALTH,
                    "amount": 1500,
                    "description": "Scheduled surgery for appendix removal, all pre-approved",
                    "incident_date": datetime.now() - timedelta(days=7),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"health": 5000},
                    "deductibles": {"health": 250},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["medical_report", "hospital_bill", "prescription"]
                },
                "user": {
                    "total_claims": 2,
                    "total_payout": 2000,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=400), "amount": 1000},
                        {"date": datetime.now() - timedelta(days=700), "amount": 1000}
                    ],
                    "account_age_days": 900,
                    "claim_frequency": 0.8,
                    "flagged_previous": False,
                    "risk_score": 0.15
                },
                "documents": {
                    "medical_report": DocumentStatus.VERIFIED,
                    "hospital_bill": DocumentStatus.VERIFIED,
                    "prescription": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "approve_claim",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
            {
                "id": "easy_004",
                "difficulty": "easy",
                "tag": "missing_docs",
                "description": "Valid claim but missing required documents",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 1800,
                    "description": "Hailstorm damage to car roof and windshield",
                    "incident_date": datetime.now() - timedelta(days=2),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["photos", "estimate", "weather_report"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 400,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.1
                },
                "documents": {
                    "photos": DocumentStatus.VERIFIED,
                    "estimate": DocumentStatus.UPLOADED,
                    "weather_report": DocumentStatus.MISSING
                },
                "ground_truth": {
                    "correct_action": "request_additional_info",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": False
                }
            },
            {
                "id": "easy_005",
                "difficulty": "easy",
                "tag": "excluded_condition",
                "description": "Claim for excluded condition",
                "claim": {
                    "claim_type": ClaimType.HEALTH,
                    "amount": 2000,
                    "description": "Treatment for pre-existing diabetes condition",
                    "incident_date": datetime.now() - timedelta(days=10),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"health": 5000},
                    "deductibles": {"health": 250},
                    "waiting_period_days": 0,
                    "excluded_conditions": ["diabetes", "pre-existing"],
                    "required_documents": ["medical_report", "hospital_bill"]
                },
                "user": {
                    "total_claims": 1,
                    "total_payout": 500,
                    "previous_claims": [{"date": datetime.now() - timedelta(days=300), "amount": 500}],
                    "account_age_days": 500,
                    "claim_frequency": 0.7,
                    "flagged_previous": False,
                    "risk_score": 0.2
                },
                "documents": {
                    "medical_report": DocumentStatus.VERIFIED,
                    "hospital_bill": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": False,
                    "has_policy_violation": True,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
        ])

        # ==================== MEDIUM SCENARIOS ====================
        scenarios.extend([
            {
                "id": "medium_001",
                "difficulty": "medium",
                "tag": "borderline_health",
                "description": "Claim at policy limit with missing docs",
                "claim": {
                    "claim_type": ClaimType.HEALTH,
                    "amount": 5000,
                    "description": "Emergency room visit for severe allergic reaction requiring overnight stay",
                    "incident_date": datetime.now() - timedelta(days=2),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"health": 5000},
                    "deductibles": {"health": 250},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["medical_report", "hospital_bill", "prescription"]
                },
                "user": {
                    "total_claims": 2,
                    "total_payout": 3200,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=200), "amount": 1500},
                        {"date": datetime.now() - timedelta(days=400), "amount": 1700}
                    ],
                    "account_age_days": 500,
                    "claim_frequency": 1.46,
                    "flagged_previous": False,
                    "risk_score": 0.4
                },
                "documents": {
                    "medical_report": DocumentStatus.UPLOADED,
                    "hospital_bill": DocumentStatus.PENDING,
                    "prescription": DocumentStatus.MISSING
                },
                "ground_truth": {
                    "correct_action": "request_additional_info",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": False
                }
            },
            {
                "id": "medium_002",
                "difficulty": "medium",
                "tag": "fraud_suspicion",
                "description": "Suspicious claim with high frequency user",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 4800,
                    "description": "Hit and run, car damaged on driver side",
                    "incident_date": datetime.now() - timedelta(days=1),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["police_report", "photos", "estimate"]
                },
                "user": {
                    "total_claims": 3,
                    "total_payout": 12500,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=30), "amount": 4500},
                        {"date": datetime.now() - timedelta(days=90), "amount": 3800},
                        {"date": datetime.now() - timedelta(days=150), "amount": 4200}
                    ],
                    "account_age_days": 200,
                    "claim_frequency": 5.475,
                    "flagged_previous": True,
                    "risk_score": 0.7
                },
                "documents": {
                    "police_report": DocumentStatus.UPLOADED,
                    "photos": DocumentStatus.UPLOADED,
                    "estimate": DocumentStatus.PENDING
                },
                "ground_truth": {
                    "correct_action": "escalate_claim",
                    "fraud_label": True,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": False
                }
            },
            {
                "id": "medium_003",
                "difficulty": "medium",
                "tag": "waiting_period",
                "description": "Claim during waiting period",
                "claim": {
                    "claim_type": ClaimType.HOME,
                    "amount": 3000,
                    "description": "Roof damage from heavy storm, tiles displaced",
                    "incident_date": datetime.now() - timedelta(days=20),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"home": 10000},
                    "deductibles": {"home": 500},
                    "waiting_period_days": 30,
                    "excluded_conditions": [],
                    "required_documents": ["photos", "contractor_estimate"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 20,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.1
                },
                "documents": {
                    "photos": DocumentStatus.VERIFIED,
                    "contractor_estimate": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": False,
                    "has_policy_violation": True,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
            {
                "id": "medium_004",
                "difficulty": "medium",
                "tag": "new_user_high_value",
                "description": "New user with suspiciously high first claim",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 4900,
                    "description": "Total loss after collision with another vehicle",
                    "incident_date": datetime.now() - timedelta(days=5),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["police_report", "photos", "estimate"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 15,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.3
                },
                "documents": {
                    "police_report": DocumentStatus.UPLOADED,
                    "photos": DocumentStatus.UPLOADED,
                    "estimate": DocumentStatus.UPLOADED
                },
                "ground_truth": {
                    "correct_action": "escalate_claim",
                    "fraud_label": True,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": True
                }
            },
            {
                "id": "medium_005",
                "difficulty": "medium",
                "tag": "rejected_documents",
                "description": "Claim with rejected documents",
                "claim": {
                    "claim_type": ClaimType.HEALTH,
                    "amount": 2500,
                    "description": "Knee surgery after sports injury during marathon",
                    "incident_date": datetime.now() - timedelta(days=14),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"health": 5000},
                    "deductibles": {"health": 250},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["medical_report", "hospital_bill", "prescription"]
                },
                "user": {
                    "total_claims": 1,
                    "total_payout": 1000,
                    "previous_claims": [{"date": datetime.now() - timedelta(days=500), "amount": 1000}],
                    "account_age_days": 600,
                    "claim_frequency": 0.6,
                    "flagged_previous": False,
                    "risk_score": 0.2
                },
                "documents": {
                    "medical_report": DocumentStatus.REJECTED,
                    "hospital_bill": DocumentStatus.VERIFIED,
                    "prescription": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "request_additional_info",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": False
                }
            },
        ])

        # ==================== HARD SCENARIOS ====================
        scenarios.extend([
            {
                "id": "hard_001",
                "difficulty": "hard",
                "tag": "conflicting_signals",
                "description": "Complex claim with mixed signals",
                "claim": {
                    "claim_type": ClaimType.HOME,
                    "amount": 9500,
                    "description": "Fire damage from electrical malfunction. Previous claim 6 months ago for similar issue.",
                    "incident_date": datetime.now() - timedelta(days=4),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"home": 10000},
                    "deductibles": {"home": 1000},
                    "waiting_period_days": 0,
                    "excluded_conditions": ["electrical_fire"],
                    "required_documents": ["fire_report", "photos", "contractor_estimate", "electrical_inspection"]
                },
                "user": {
                    "total_claims": 2,
                    "total_payout": 8800,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=180), "amount": 8800, "type": "electrical_fire"}
                    ],
                    "account_age_days": 365,
                    "claim_frequency": 2.0,
                    "flagged_previous": True,
                    "risk_score": 0.6
                },
                "documents": {
                    "fire_report": DocumentStatus.VERIFIED,
                    "photos": DocumentStatus.VERIFIED,
                    "contractor_estimate": DocumentStatus.UPLOADED,
                    "electrical_inspection": DocumentStatus.MISSING
                },
                "ground_truth": {
                    "correct_action": "escalate_claim",
                    "fraud_label": True,
                    "has_policy_violation": True,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": False
                }
            },
            {
                "id": "hard_002",
                "difficulty": "hard",
                "tag": "sophisticated_fraud",
                "description": "Sophisticated fraud with professional documentation",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 4950,
                    "description": "Multi-vehicle collision on highway, extensive damage to front and side. All documentation provided.",
                    "incident_date": datetime.now() - timedelta(days=10),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["police_report", "photos", "estimate", "witness_statements"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 25,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.1
                },
                "documents": {
                    "police_report": DocumentStatus.VERIFIED,
                    "photos": DocumentStatus.VERIFIED,
                    "estimate": DocumentStatus.VERIFIED,
                    "witness_statements": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": True,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": True
                }
            },
            {
                "id": "hard_003",
                "difficulty": "hard",
                "tag": "life_claim_complex",
                "description": "Life insurance claim with suspicious timing",
                "claim": {
                    "claim_type": ClaimType.LIFE,
                    "amount": 45000,
                    "description": "Accidental death claim filed by beneficiary",
                    "incident_date": datetime.now() - timedelta(days=8),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"life": 50000},
                    "deductibles": {"life": 0},
                    "waiting_period_days": 0,
                    "excluded_conditions": ["suicide"],
                    "required_documents": ["death_certificate", "autopsy_report", "police_report", "beneficiary_id"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 45,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.4
                },
                "documents": {
                    "death_certificate": DocumentStatus.VERIFIED,
                    "autopsy_report": DocumentStatus.PENDING,
                    "police_report": DocumentStatus.UPLOADED,
                    "beneficiary_id": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "escalate_claim",
                    "fraud_label": True,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": False
                }
            },
            {
                "id": "hard_004",
                "difficulty": "hard",
                "tag": "multi_violation",
                "description": "Multiple policy violations simultaneously",
                "claim": {
                    "claim_type": ClaimType.HOME,
                    "amount": 12000,
                    "description": "Flood damage to basement and ground floor",
                    "incident_date": datetime.now() - timedelta(days=3),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"home": 10000},
                    "deductibles": {"home": 1000},
                    "waiting_period_days": 14,
                    "excluded_conditions": ["flood", "natural_disaster"],
                    "required_documents": ["photos", "contractor_estimate", "flood_report"]
                },
                "user": {
                    "total_claims": 4,
                    "total_payout": 35000,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=60), "amount": 9000},
                        {"date": datetime.now() - timedelta(days=120), "amount": 8500},
                        {"date": datetime.now() - timedelta(days=200), "amount": 9500},
                        {"date": datetime.now() - timedelta(days=300), "amount": 8000}
                    ],
                    "account_age_days": 400,
                    "claim_frequency": 3.65,
                    "flagged_previous": True,
                    "risk_score": 0.85
                },
                "documents": {
                    "photos": DocumentStatus.VERIFIED,
                    "contractor_estimate": DocumentStatus.VERIFIED,
                    "flood_report": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": True,
                    "has_policy_violation": True,
                    "amount_valid": False,
                    "user_high_risk": True,
                    "docs_complete": True
                }
            },
            {
                "id": "hard_005",
                "difficulty": "hard",
                "tag": "legitimate_high_value",
                "description": "Legitimate high value claim that looks suspicious",
                "claim": {
                    "claim_type": ClaimType.HOME,
                    "amount": 9800,
                    "description": "Extensive fire damage to kitchen and living room from accidental gas leak",
                    "incident_date": datetime.now() - timedelta(days=6),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"home": 10000},
                    "deductibles": {"home": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["fire_report", "photos", "contractor_estimate", "gas_company_report"]
                },
                "user": {
                    "total_claims": 1,
                    "total_payout": 2000,
                    "previous_claims": [{"date": datetime.now() - timedelta(days=800), "amount": 2000}],
                    "account_age_days": 1200,
                    "claim_frequency": 0.3,
                    "flagged_previous": False,
                    "risk_score": 0.2
                },
                "documents": {
                    "fire_report": DocumentStatus.VERIFIED,
                    "photos": DocumentStatus.VERIFIED,
                    "contractor_estimate": DocumentStatus.VERIFIED,
                    "gas_company_report": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "approve_claim",
                    "fraud_label": False,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
            {
                "id": "hard_006",
                "difficulty": "hard",
                "tag": "identity_fraud",
                "description": "Potential identity fraud with inconsistent details",
                "claim": {
                    "claim_type": ClaimType.HEALTH,
                    "amount": 4800,
                    "description": "Emergency surgery, patient details inconsistent with policy records",
                    "incident_date": datetime.now() - timedelta(days=1),
                    "severity": "high"
                },
                "policy": {
                    "coverage_limits": {"health": 5000},
                    "deductibles": {"health": 250},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["medical_report", "hospital_bill", "id_proof"]
                },
                "user": {
                    "total_claims": 0,
                    "total_payout": 0,
                    "previous_claims": [],
                    "account_age_days": 10,
                    "claim_frequency": 0,
                    "flagged_previous": False,
                    "risk_score": 0.5
                },
                "documents": {
                    "medical_report": DocumentStatus.UPLOADED,
                    "hospital_bill": DocumentStatus.UPLOADED,
                    "id_proof": DocumentStatus.REJECTED
                },
                "ground_truth": {
                    "correct_action": "escalate_claim",
                    "fraud_label": True,
                    "has_policy_violation": False,
                    "amount_valid": True,
                    "user_high_risk": True,
                    "docs_complete": False
                }
            },
            {
                "id": "hard_007",
                "difficulty": "hard",
                "tag": "inactive_policy",
                "description": "Claim on inactive policy",
                "claim": {
                    "claim_type": ClaimType.AUTO,
                    "amount": 3500,
                    "description": "Side collision in parking lot causing door and panel damage",
                    "incident_date": datetime.now() - timedelta(days=2),
                    "severity": "medium"
                },
                "policy": {
                    "coverage_limits": {"auto": 5000},
                    "deductibles": {"auto": 500},
                    "waiting_period_days": 0,
                    "excluded_conditions": [],
                    "required_documents": ["police_report", "photos", "estimate"]
                },
                "user": {
                    "total_claims": 2,
                    "total_payout": 5000,
                    "previous_claims": [
                        {"date": datetime.now() - timedelta(days=300), "amount": 2500},
                        {"date": datetime.now() - timedelta(days=600), "amount": 2500}
                    ],
                    "account_age_days": 700,
                    "claim_frequency": 1.0,
                    "flagged_previous": False,
                    "risk_score": 0.3
                },
                "documents": {
                    "police_report": DocumentStatus.VERIFIED,
                    "photos": DocumentStatus.VERIFIED,
                    "estimate": DocumentStatus.VERIFIED
                },
                "ground_truth": {
                    "correct_action": "reject_claim",
                    "fraud_label": False,
                    "has_policy_violation": True,
                    "amount_valid": True,
                    "user_high_risk": False,
                    "docs_complete": True
                }
            },
        ])

        # Mark inactive policy for hard_007
        for s in scenarios:
            if s["id"] == "hard_007":
                s["policy"]["active"] = False

        return scenarios

    def get_scenario(self, scenario_id: str = None, difficulty: str = None) -> Dict[str, Any]:
        if scenario_id:
            scenario = next((s for s in self.scenarios if s["id"] == scenario_id), None)
            if scenario:
                return scenario

        if difficulty:
            filtered = [s for s in self.scenarios if s["difficulty"] == difficulty]
            if filtered:
                import random
                return random.choice(filtered)

        import random
        return random.choice(self.scenarios)

    def get_all_scenario_ids(self) -> List[str]:
        return [s["id"] for s in self.scenarios]

    def get_scenarios_by_difficulty(self, difficulty: str) -> List[Dict[str, Any]]:
        return [s for s in self.scenarios if s["difficulty"] == difficulty]