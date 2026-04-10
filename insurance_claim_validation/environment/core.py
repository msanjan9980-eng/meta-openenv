# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Insurance claim validation environment (OpenEnv Gym-style semantics)."""

from __future__ import annotations

import copy
import random
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from openenv.core.env_server.interfaces import Environment
from openenv.core.env_server.types import State

from insurance_claim_validation.models import ClaimAction, ClaimObservation
from insurance_claim_validation.environment.rule_engine import PolicyRuleEngine
from insurance_claim_validation.environment.scenarios import ScenarioGenerator
from insurance_claim_validation.environment.schemas import (
    ClaimDetails,
    ClaimType,
    Document,
    DocumentStatus,
    PolicyInfo,
    RiskSignal,
    UserHistory,
)
from insurance_claim_validation.environment.rewards import (
    aggregate_episode_reward,
    compute_final_outcome_reward,
    compute_step_reward,
    docs_complete_from_documents,
    squeeze_to_open_interval,
)
from insurance_claim_validation.environment.stochastic import perturb_scenario_for_episode


class InsuranceClaimEnvironment(Environment[ClaimAction, ClaimObservation, State]):
    """Multi-step claim validation with partial observations and validator-safe rewards."""

    SUPPORTS_CONCURRENT_SESSIONS = True

    def __init__(self, config: Optional[Dict[str, Any]] = None) -> None:
        super().__init__()
        self.config = config or {}
        self.max_steps: int = int(self.config.get("max_steps", 6))
        self.rule_engine = PolicyRuleEngine()
        self.scenario_gen = ScenarioGenerator()

        self._scenario_template: Optional[Dict[str, Any]] = None
        self._scenario: Optional[Dict[str, Any]] = None
        self._rng: random.Random = random.Random()
        self._state = State(episode_id=str(uuid4()), step_count=0)
        self._done = False
        self._action_history: List[ClaimAction] = []
        self._revealed: Set[str] = set()
        self._step_rewards_canonical: List[float] = []
        self._documents: Dict[str, Document] = {}
        self._risk_signals: List[RiskSignal] = []
        self.last_step_info: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs: Any,
    ) -> ClaimObservation:
        scenario_id = kwargs.get("scenario_id")
        difficulty = kwargs.get("difficulty")

        self._rng = random.Random(seed if seed is not None else random.randrange(2**31))
        base = self.scenario_gen.get_scenario(scenario_id, difficulty)
        self._scenario_template = copy.deepcopy(base)
        self._scenario = perturb_scenario_for_episode(base, self._rng)

        self._state = State(
            episode_id=episode_id or str(uuid4()),
            step_count=0,
        )
        self._done = False
        self._action_history = []
        self._revealed = {"claim"}
        self._step_rewards_canonical = []
        self._reset_rubric()

        self._documents = self._build_documents_from_scenario(self._scenario)
        self._risk_signals = self._parse_risk_signals(self._scenario.get("risk_signals", []))

        obs = self._make_observation()
        obs.reward = squeeze_to_open_interval(0.5)
        obs.done = False
        obs.metadata = {
            "scenario_id": self._scenario["id"],
            "difficulty": self._scenario["difficulty"],
            "tag": self._scenario["tag"],
            "episode_id": self._state.episode_id,
        }
        self.last_step_info = {}
        return self._apply_transform(obs)

    def step(
        self,
        action: ClaimAction,
        timeout_s: Optional[float] = None,
        **kwargs: Any,
    ) -> ClaimObservation:
        if self._done or self._scenario is None:
            raise RuntimeError("Episode finished; call reset().")

        prev = self._action_history[-1].action if self._action_history else None
        self._action_history.append(action)
        self._state = State(
            episode_id=self._state.episode_id,
            step_count=self._state.step_count + 1,
        )

        self._process_action(action)

        gt = self._scenario_template["ground_truth"]
        complete = docs_complete_from_documents(
            {k: v.model_dump() for k, v in self._documents.items()},
            list(self._scenario["policy"]["required_documents"]),
        )
        r_step_canon, step_comp = compute_step_reward(action, prev, gt, complete)
        self._step_rewards_canonical.append(r_step_canon)

        terminal_actions = {
            "approve_claim",
            "reject_claim",
            "escalate_claim",
        }
        hit_limit = self._state.step_count >= self.max_steps
        terminal = action.action in terminal_actions or hit_limit

        if terminal:
            self._done = True
            r_final_canon, final_comp = compute_final_outcome_reward(
                self._action_history,
                gt,
                self._state.step_count,
                self.max_steps,
            )
            # Average step quality excludes terminal step to avoid double-counting decisions
            pre_terminal = (
                self._step_rewards_canonical[:-1]
                if len(self._step_rewards_canonical) >= 1
                else []
            )
            episode_canon = aggregate_episode_reward(pre_terminal, r_final_canon)
            total = squeeze_to_open_interval(episode_canon)

            info = {
                "decision": final_comp["decision"],
                "fraud_detection": final_comp["fraud_detection"],
                "reasoning": final_comp["reasoning"],
                "efficiency": final_comp["efficiency"],
                "sequence_readiness": final_comp.get("sequence_readiness"),
                "canonical_episode": episode_canon,
                "canonical_final_outcome": r_final_canon,
                "reward_squeezed": total,
                "avg_step_canonical": (
                    sum(pre_terminal) / len(pre_terminal) if pre_terminal else None
                ),
                "step_components_last": step_comp,
                "final_components": final_comp,
            }
            self.last_step_info = info
            obs = self._make_observation()
            obs.reward = total
            obs.done = True
            obs.metadata = {
                **(obs.metadata or {}),
                "scenario_id": self._scenario["id"],
                "difficulty": self._scenario["difficulty"],
                "tag": self._scenario["tag"],
                "episode_id": self._state.episode_id,
                "reward_info": info,
            }
            return self._apply_transform(obs)

        self.last_step_info = {
            "step_components": step_comp,
            "canonical_step": r_step_canon,
            "reward_squeezed": squeeze_to_open_interval(r_step_canon),
        }
        obs = self._make_observation()
        obs.reward = squeeze_to_open_interval(r_step_canon)
        obs.done = False
        obs.metadata = {
            "scenario_id": self._scenario["id"],
            "difficulty": self._scenario["difficulty"],
            "tag": self._scenario["tag"],
            "episode_id": self._state.episode_id,
            "step_components": step_comp,
        }
        return self._apply_transform(obs)

    @property
    def state(self) -> State:
        return self._state

    # ------------------------------------------------------------------
    def _build_documents_from_scenario(self, scenario: Dict[str, Any]) -> Dict[str, Document]:
        out: Dict[str, Document] = {}
        for name, st in scenario["documents"].items():
            status = st if isinstance(st, DocumentStatus) else DocumentStatus(st)
            out[name] = Document(doc_type=name, status=status)
        return out

    def _parse_risk_signals(self, raw: List[Any]) -> List[RiskSignal]:
        out: List[RiskSignal] = []
        for item in raw:
            if isinstance(item, RiskSignal):
                out.append(item)
            else:
                out.append(RiskSignal(**item))
        return out

    def _process_action(self, action: ClaimAction) -> None:
        assert self._scenario is not None
        name = action.action
        if name == "analyze_claim":
            self._revealed.update({"policy", "user", "violations"})
        elif name == "detect_fraud_signals":
            self._revealed.update({"policy", "user", "risk", "violations"})
            self._risk_signals.append(
                RiskSignal(
                    signal_type="agent_analysis",
                    description="Desk review triggered (model-assisted)",
                    severity=min(
                        0.94,
                        max(
                            0.08,
                            0.45 + 0.07 * len(action.reasoning.fraud_indicators),
                        ),
                    ),
                )
            )
        elif name == "request_additional_info":
            self._revealed.update({"policy", "user", "docs"})
            for req in self._scenario["policy"]["required_documents"]:
                if req not in self._documents:
                    self._documents[req] = Document(doc_type=req, status=DocumentStatus.UPLOADED)
                elif self._documents[req].status in (
                    DocumentStatus.MISSING,
                    DocumentStatus.PENDING,
                ):
                    self._documents[req].status = DocumentStatus.UPLOADED

    def _mask_user(self, full: Dict[str, Any]) -> UserHistory:
        u = copy.deepcopy(full)
        if "user" not in self._revealed:
            u["previous_claims"] = []
        return UserHistory(user_id=f"USER_{self._scenario['id']}", **u)

    def _mask_policy(self, full: Dict[str, Any]) -> PolicyInfo:
        p = copy.deepcopy(full)
        if "policy" not in self._revealed:
            p["excluded_conditions"] = []
        return PolicyInfo(policy_id=f"POL_{self._scenario['id']}", **p)

    def _visible_risk_signals(self) -> List[RiskSignal]:
        if "risk" in self._revealed:
            return list(self._risk_signals)
        return self._risk_signals[:1]

    def _make_observation(self) -> ClaimObservation:
        assert self._scenario is not None
        sc = self._scenario
        claim_d = sc["claim"].copy()
        if not isinstance(claim_d["claim_type"], ClaimType):
            claim_d["claim_type"] = ClaimType(claim_d["claim_type"])
        claim = ClaimDetails(**claim_d)

        policy = self._mask_policy(sc["policy"])
        user = self._mask_user(sc["user"])

        uw: Dict[str, float] = {}
        if "violations" in self._revealed:
            full_pol = PolicyInfo(
                policy_id=f"POL_{sc['id']}", **copy.deepcopy(sc["policy"])
            )
            full_user = UserHistory(
                user_id=f"USER_{sc['id']}", **copy.deepcopy(sc["user"])
            )
            temp_full = ClaimObservation(
                claim=claim,
                policy=full_pol,
                user_history=full_user,
                documents=self._documents,
                risk_signals=self._risk_signals,
                policy_violations=[],
                underwriting_signals={},
                done=False,
                reward=0.0,
            )
            uw = self.rule_engine.underwriting_signal_scores(temp_full, self._rng)

        obs = ClaimObservation(
            claim=claim,
            policy=policy,
            user_history=user,
            documents=copy.deepcopy(self._documents),
            risk_signals=self._visible_risk_signals(),
            derived_signals={
                "last_action": self._action_history[-1].action
                if self._action_history
                else None
            },
            policy_violations=[],
            underwriting_signals=uw,
            step_count=self._state.step_count,
            action_history=[a.action for a in self._action_history],
            partial_observation=len(self._revealed) < 4,
            revealed_facets=sorted(self._revealed),
            done=False,
            reward=0.0,
            metadata={},
        )
        return obs
