"""Validator-style checks: open-interval rewards, no label leakage, robustness."""

from __future__ import annotations

import random

import pytest

from insurance_claim_validation import ClaimAction, InsuranceClaimEnvironment
from insurance_claim_validation.environment.rewards import REWARD_EPS, squeeze_to_open_interval
from insurance_claim_validation.environment.schemas import ReasoningOutput


def _r(**kwargs):
    base = dict(
        policy_violation=False,
        claim_amount_valid=True,
        user_risk_high=False,
        documents_complete=True,
        fraud_indicators=[],
        confidence=0.7,
        recommendation=None,
    )
    base.update(kwargs)
    return ReasoningOutput(**base)


def test_reward_strictly_inside_unit_interval_many_episodes():
    rng = random.Random(42)
    actions = [
        "analyze_claim",
        "detect_fraud_signals",
        "request_additional_info",
        "approve_claim",
        "reject_claim",
        "escalate_claim",
        "ignore",
    ]
    for _ in range(80):
        env = InsuranceClaimEnvironment({"max_steps": 6})
        obs = env.reset(seed=rng.randint(0, 10_000))
        assert REWARD_EPS < (obs.reward or 0) < 1.0 - REWARD_EPS
        for _s in range(24):
            a = rng.choice(actions)
            obs = env.step(ClaimAction(action=a, reasoning=_r()))
            assert REWARD_EPS < (obs.reward or 0) < 1.0 - REWARD_EPS
            if obs.done:
                assert "ground_truth" not in (obs.metadata or {})
                break
        else:
            pytest.fail("episode did not terminate")


def test_squeeze_never_hits_exact_zero_or_one():
    for x in [0.0, 0.25, 0.5, 0.75, 1.0]:
        y = squeeze_to_open_interval(x)
        assert REWARD_EPS < y < 1.0 - REWARD_EPS


def test_observation_has_no_ground_truth_metadata():
    env = InsuranceClaimEnvironment({"max_steps": 4})
    env.reset(scenario_id="easy_001", seed=123)
    obs = env.step(ClaimAction(action="approve_claim", reasoning=_r(recommendation="approve_claim")))
    assert obs.done
    assert "ground_truth" not in (obs.metadata or {})


def test_underwriting_signals_not_empty_after_analyze():
    env = InsuranceClaimEnvironment({"max_steps": 6})
    env.reset(scenario_id="easy_001", seed=7)
    obs = env.step(ClaimAction(action="analyze_claim", reasoning=_r()))
    assert obs.policy_violations == []
    assert isinstance(obs.underwriting_signals, dict)
    assert len(obs.underwriting_signals) > 0


def test_separate_env_instances_no_shared_mutable_state():
    e1 = InsuranceClaimEnvironment({"max_steps": 3})
    e2 = InsuranceClaimEnvironment({"max_steps": 3})
    e1.reset(scenario_id="easy_001", seed=99)
    e2.reset(scenario_id="medium_001", seed=100)
    assert e1._scenario["id"] != e2._scenario["id"]
