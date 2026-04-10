import pytest

from insurance_claim_validation import ClaimAction, InsuranceClaimEnvironment
from insurance_claim_validation.environment.schemas import ReasoningOutput


def _r(**kwargs):
    base = dict(
        policy_violation=False,
        claim_amount_valid=True,
        user_risk_high=False,
        documents_complete=True,
        fraud_indicators=[],
        confidence=0.8,
        recommendation=None,
    )
    base.update(kwargs)
    return ReasoningOutput(**base)


def test_episode_terminates_and_reward_bounded():
    env = InsuranceClaimEnvironment({"max_steps": 6})
    env.reset(scenario_id="easy_001")
    obs = env.step(ClaimAction(action="analyze_claim", reasoning=_r()))
    assert obs.done is False
    assert 0.0 <= (obs.reward or 0) <= 1.0
    obs = env.step(ClaimAction(action="approve_claim", reasoning=_r(recommendation="approve_claim")))
    assert obs.done is True
    assert 0.0 <= (obs.reward or 0) <= 1.0


def test_max_steps_forces_terminal():
    env = InsuranceClaimEnvironment({"max_steps": 2})
    env.reset(scenario_id="easy_001")
    env.step(ClaimAction(action="analyze_claim", reasoning=_r()))
    obs = env.step(ClaimAction(action="analyze_claim", reasoning=_r()))
    assert obs.done is True


def test_scenario_count():
    from insurance_claim_validation.environment.scenarios import ScenarioGenerator

    gen = ScenarioGenerator()
    assert len(gen.scenarios) == 18
