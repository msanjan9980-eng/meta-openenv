# Insurance Claim Validation Environment
from environment.core import InsuranceClaimEnvironment

try:
    from models import ClaimAction, ClaimObservation
except ImportError:
    from environment.schemas import ClaimAction, ClaimObservation

MyEnv2Action = ClaimAction
MyEnv2Observation = ClaimObservation
MyEnv2Environment = InsuranceClaimEnvironment

__all__ = [
    "InsuranceClaimEnvironment",
    "MyEnv2Environment",
    "ClaimAction",
    "ClaimObservation",
    "MyEnv2Action",
    "MyEnv2Observation",
]
