# Copyright (c) Meta Platforms, Inc. and affiliates.
#
# SPDX-License-Identifier: BSD-3-Clause

"""WebSocket client for the insurance claim validation environment."""

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from insurance_claim_validation.models import ClaimAction, ClaimObservation


class InsuranceClaimEnvClient(EnvClient[ClaimAction, ClaimObservation, State]):
    """Connects to ``/ws`` (OpenEnv protocol). Use ``async with`` or ``.sync()``."""

    def _step_payload(self, action: ClaimAction) -> Dict[str, Any]:
        return action.model_dump(mode="json")

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[ClaimObservation]:
        obs_fields = dict(payload.get("observation") or {})
        obs_fields["reward"] = payload.get("reward")
        obs_fields["done"] = payload.get("done", False)
        observation = ClaimObservation.model_validate(obs_fields)
        return StepResult(
            observation=observation,
            reward=payload.get("reward"),
            done=payload.get("done", False),
        )

    def _parse_state(self, payload: Dict[str, Any]) -> State:
        return State(
            episode_id=payload.get("episode_id"),
            step_count=payload.get("step_count", 0),
        )
