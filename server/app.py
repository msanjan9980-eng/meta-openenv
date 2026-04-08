"""
Insurance claim validation server — OpenEnv HTTP + WebSocket API.
 
Stateful multi-step episodes require WebSocket ``/ws`` (or the EnvClient).
Stateless ``POST /reset`` and ``POST /step`` from OpenEnv create a fresh
environment per request; use this module's ``/episode/*`` routes for HTTP
sessions keyed by ``session_id``.
"""
 
from __future__ import annotations
 
from datetime import datetime
from typing import Any, Dict, List, Optional
 
from fastapi import Body, FastAPI
from pydantic import BaseModel
 
from openenv.core.env_server import create_app
 
try:
    from environment.core import InsuranceClaimEnvironment
    from environment.scenarios import ScenarioGenerator
    from environment.schemas import ClaimAction, ClaimObservation
except ImportError:
    from environment.core import InsuranceClaimEnvironment
    from environment.scenarios import ScenarioGenerator
    from environment.schemas import ClaimAction, ClaimObservation
 
 
def _make_env() -> InsuranceClaimEnvironment:
    return InsuranceClaimEnvironment({"max_steps": 6})
 
 
# create_fastapi_app registers the required OpenEnv endpoints:
#   POST /reset, POST /step, GET /state, GET /health, WS /ws/{session_id}
app: FastAPI = create_app(
    _make_env,
    ClaimAction,
    ClaimObservation,
    max_concurrent_envs=8,
)
 
# ---------------------------------------------------------------------------
# Stateful HTTP API (session_id keyed) — for demos and simple HTTP clients
# ---------------------------------------------------------------------------
 
_episode_envs: Dict[str, InsuranceClaimEnvironment] = {}
_episode_histories: Dict[str, List[Dict[str, Any]]] = {}
_global_stats: Dict[str, Any] = {
    "total_episodes": 0,
    "total_steps": 0,
}
 
 
def _get_episode_env(session_id: str) -> InsuranceClaimEnvironment:
    if session_id not in _episode_envs:
        _episode_envs[session_id] = InsuranceClaimEnvironment({"max_steps": 6})
    return _episode_envs[session_id]
 
 
class EpisodeResetBody(BaseModel):
    session_id: str = "default"
    scenario_id: Optional[str] = None
    difficulty: Optional[str] = None
 
 
class EpisodeStepBody(BaseModel):
    session_id: str = "default"
    action: Dict[str, Any]
 
 
@app.post("/episode/reset")
def episode_reset(
    body: EpisodeResetBody = Body(default_factory=EpisodeResetBody),
) -> Dict[str, Any]:
    env = _get_episode_env(body.session_id)
    _episode_histories[body.session_id] = []
    obs = env.reset(scenario_id=body.scenario_id, difficulty=body.difficulty)
    return {
        **obs.model_dump(mode="json"),
        "reward": obs.reward,
        "done": obs.done,
    }
 
 
@app.post("/episode/step")
def episode_step(body: EpisodeStepBody) -> Dict[str, Any]:
    env = _get_episode_env(body.session_id)
    action = ClaimAction.model_validate(body.action)
    obs = env.step(action)
    info = env.last_step_info
 
    if body.session_id not in _episode_histories:
        _episode_histories[body.session_id] = []
    _episode_histories[body.session_id].append(
        {"action": action.model_dump(mode="json"), "reward": obs.reward, "done": obs.done}
    )
 
    _global_stats["total_steps"] += 1
    if obs.done:
        _global_stats["total_episodes"] += 1
 
    return {
        "observation": obs.model_dump(mode="json"),
        "reward": obs.reward,
        "done": obs.done,
        "info": info,
    }
 
 
@app.get("/scenarios")
def list_scenarios() -> Dict[str, Any]:
    gen = ScenarioGenerator()
    return {
        "total": len(gen.scenarios),
        "by_difficulty": {
            "easy": [s["id"] for s in gen.get_scenarios_by_difficulty("easy")],
            "medium": [s["id"] for s in gen.get_scenarios_by_difficulty("medium")],
            "hard": [s["id"] for s in gen.get_scenarios_by_difficulty("hard")],
        },
        "all_ids": gen.get_all_scenario_ids(),
    }
 
 
@app.get("/scenarios/filter")
def filter_scenarios(
    tag: Optional[str] = None,
    difficulty: Optional[str] = None,
) -> Dict[str, Any]:
    gen = ScenarioGenerator()
    filtered = gen.scenarios
    if difficulty:
        filtered = [s for s in filtered if s["difficulty"] == difficulty]
    if tag:
        filtered = [s for s in filtered if tag in s["tag"]]
    return {
        "total": len(filtered),
        "scenarios": [
            {
                "id": s["id"],
                "difficulty": s["difficulty"],
                "tag": s["tag"],
                "description": s["description"],
            }
            for s in filtered
        ],
    }
 
 
@app.get("/environment/stats")
def environment_stats() -> Dict[str, Any]:
    return {
        "total_episodes": _global_stats["total_episodes"],
        "total_steps": _global_stats["total_steps"],
        "active_sessions": len(_episode_envs),
        "timestamp": datetime.now().isoformat(),
    }
 
 
# FIX: default port is 7860 to match Dockerfile CMD and HF Spaces requirement

# Entry point — port 7860 matches HF Spaces requirement
def main(host: str = "0.0.0.0", port: int = 7860) -> None:
    import uvicorn
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
