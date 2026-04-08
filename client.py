# Copyright (c) Meta Platforms, Inc. and affiliates.
# All rights reserved.
#
# This source code is licensed under the BSD-style license found in the
# LICENSE file in the root directory of this source tree.

"""OpenEnv WebSocket client for the insurance claim validation environment."""

from typing import Any, Dict

from openenv.core import EnvClient
from openenv.core.client_types import StepResult
from openenv.core.env_server.types import State

from .models import MyEnv2Action, MyEnv2Observation


class MyEnv2Env(EnvClient[MyEnv2Action, MyEnv2Observation, State]):
    """
    Client for the insurance claim validation environment.

    Connects to the server WebSocket at ``/ws`` (OpenEnv protocol). Use
    ``async with MyEnv2Env(base_url=...)`` or ``MyEnv2Env(...).sync()`` for
    synchronous code.

    Use ``reset(**kwargs)`` to pass ``difficulty`` / ``scenario_id``, and
    ``step(MyEnv2Action(...))`` for each decision.
    """

    def _step_payload(self, action: MyEnv2Action) -> Dict[str, Any]:
        return action.model_dump(mode="json")

    def _parse_result(self, payload: Dict[str, Any]) -> StepResult[MyEnv2Observation]:
        obs_fields = dict(payload.get("observation") or {})
        obs_fields["reward"] = payload.get("reward")
        obs_fields["done"] = payload.get("done", False)
        observation = MyEnv2Observation.model_validate(obs_fields)
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
