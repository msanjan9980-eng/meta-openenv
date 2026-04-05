from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Any, Dict, List, Optional
from datetime import datetime
from environment.core import InsuranceClaimEnvironment
from environment.schemas import ClaimAction, ReasoningOutput
import json
import uuid

app = FastAPI(
    title="Insurance Claim Validation Environment",
    description="OpenEnv-compatible RL environment for insurance claim validation with fraud detection",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store multiple environments for concurrent sessions
environments: Dict[str, InsuranceClaimEnvironment] = {}
episode_histories: Dict[str, List[Dict]] = {}
leaderboard: List[Dict] = []
episode_replays: Dict[str, List[Dict]] = {}
difficulty_tracker: Dict[str, str] = {}
environment_stats: Dict[str, Any] = {
    "total_episodes": 0,
    "total_steps": 0,
    "total_approved": 0,
    "total_rejected": 0,
    "total_escalated": 0,
    "total_fraud_detected": 0,
    "avg_reward": 0.0,
    "all_rewards": []
}

def get_or_create_env(session_id: str) -> InsuranceClaimEnvironment:
    if session_id not in environments:
        environments[session_id] = InsuranceClaimEnvironment({"max_steps": 6})
    return environments[session_id]

@app.get("/")
def root():
    return {
        "name": "Insurance Claim Validation Environment",
        "version": "3.0.0",
        "description": "OpenEnv-compatible RL environment for insurance claim validation",
        "endpoints": {
            "POST /reset": "Reset environment",
            "POST /step": "Take a step",
            "GET /state": "Current state",
            "GET /schema": "Action/observation schemas",
            "GET /health": "Health check",
            "GET /scenarios": "List all scenarios",
            "GET /scenarios/filter": "Filter scenarios by tag or difficulty",
            "GET /metrics": "Episode metrics",
            "GET /stats": "Global environment statistics",
            "GET /replay/{session_id}": "Replay episode",
            "POST /leaderboard": "Submit score",
            "GET /leaderboard": "Get leaderboard",
            "WS /ws/{session_id}": "WebSocket connection"
        }
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(environments),
        "version": "2.0.0"
    }

@app.get("/schema")
def schema():
    return {
        "action_space": {
            "type": "structured",
            "actions": [
                "analyze_claim",
                "detect_fraud_signals",
                "approve_claim",
                "reject_claim",
                "escalate_claim",
                "request_additional_info",
                "ignore"
            ],
            "reasoning_fields": {
                "policy_violation": "bool",
                "claim_amount_valid": "bool",
                "user_risk_high": "bool",
                "documents_complete": "bool",
                "fraud_indicators": "list[str]",
                "confidence": "float [0.0, 1.0]",
                "recommendation": "str"
            }
        },
        "observation_space": {
            "type": "structured",
            "fields": {
                "claim": "ClaimDetails",
                "policy": "PolicyInfo",
                "user_history": "UserHistory",
                "documents": "Dict[str, Document]",
                "risk_signals": "List[RiskSignal]",
                "policy_violations": "List[str]",
                "step_count": "int"
            }
        },
        "reward_range": [0.0, 1.0],
        "max_steps": 6,
        "difficulty_levels": ["easy", "medium", "hard"]
    }

@app.get("/scenarios")
def list_scenarios():
    from environment.scenarios import ScenarioGenerator
    gen = ScenarioGenerator()
    return {
        "total": len(gen.scenarios),
        "by_difficulty": {
            "easy": [s["id"] for s in gen.get_scenarios_by_difficulty("easy")],
            "medium": [s["id"] for s in gen.get_scenarios_by_difficulty("medium")],
            "hard": [s["id"] for s in gen.get_scenarios_by_difficulty("hard")]
        },
        "all_ids": gen.get_all_scenario_ids()
    }

class ResetRequest(BaseModel):
    scenario_id: Optional[str] = None
    difficulty: Optional[str] = None
    session_id: Optional[str] = None

class StepRequest(BaseModel):
    action: ClaimAction
    session_id: Optional[str] = None

@app.post("/reset")
def reset(request: ResetRequest = None):
    if request is None:
        request = ResetRequest()
    session_id = request.session_id or "default"
    env = get_or_create_env(session_id)
    episode_histories[session_id] = []
    obs = env.reset(
        scenario_id=request.scenario_id,
        difficulty=request.difficulty
    )
    return obs.dict()

@app.post("/step")
def step(request: StepRequest):
    session_id = request.session_id or "default"
    env = get_or_create_env(session_id)
    obs, reward, done, info = env.step(request.action)
    result = {
        "observation": obs.dict(),
        "reward": reward,
        "done": done,
        "info": info
    }
    if session_id not in episode_histories:
        episode_histories[session_id] = []
    if session_id not in episode_replays:
        episode_replays[session_id] = []

    step_record = {
        "step": info["step"],
        "action": request.action.dict(),
        "reward": reward,
        "done": done,
        "observation": obs.dict(),
        "timestamp": datetime.now().isoformat()
    }
    episode_histories[session_id].append({
        "action": request.action.dict(),
        "reward": reward,
        "done": done
    })
    episode_replays[session_id].append(step_record)

    # Update global stats
    environment_stats["total_steps"] += 1
    action_name = request.action.action
    if action_name == "approve_claim":
        environment_stats["total_approved"] += 1
    elif action_name == "reject_claim":
        environment_stats["total_rejected"] += 1
    elif action_name == "escalate_claim":
        environment_stats["total_escalated"] += 1
    if request.action.reasoning.fraud_indicators:
        environment_stats["total_fraud_detected"] += 1

    if done:
        environment_stats["total_episodes"] += 1
        environment_stats["all_rewards"].append(reward)
        environment_stats["avg_reward"] = sum(
            environment_stats["all_rewards"]) / len(environment_stats["all_rewards"])

        # Auto-scale difficulty
        history = episode_histories.get(session_id, [])
        rewards = [h["reward"] for h in history]
        avg = sum(rewards) / len(rewards) if rewards else 0
        current_difficulty = difficulty_tracker.get(session_id, "easy")
        if avg > 0.8 and current_difficulty == "easy":
            difficulty_tracker[session_id] = "medium"
        elif avg > 0.8 and current_difficulty == "medium":
            difficulty_tracker[session_id] = "hard"

    return result

@app.get("/state")
def state(session_id: str = "default"):
    env = get_or_create_env(session_id)
    return env.state()

@app.get("/metrics")
def metrics(session_id: str = "default"):
    history = episode_histories.get(session_id, [])
    if not history:
        return {"message": "No episode history available"}
    rewards = [h["reward"] for h in history]
    return {
        "session_id": session_id,
        "total_steps": len(history),
        "total_reward": sum(rewards),
        "average_reward": sum(rewards) / len(rewards),
        "max_reward": max(rewards),
        "min_reward": min(rewards),
        "actions_taken": [h["action"]["action"] for h in history]
    }

@app.post("/leaderboard")
def submit_score(session_id: str = "default", agent_name: str = "anonymous"):
    history = episode_histories.get(session_id, [])
    if not history:
        return {"message": "No episode history available"}
    rewards = [h["reward"] for h in history]
    total_reward = sum(rewards)
    avg_reward = total_reward / len(rewards)
    entry = {
        "agent_name": agent_name,
        "session_id": session_id,
        "total_steps": len(history),
        "total_reward": round(total_reward, 3),
        "avg_reward": round(avg_reward, 3),
        "timestamp": datetime.now().isoformat()
    }
    leaderboard.append(entry)
    leaderboard.sort(key=lambda x: x["total_reward"], reverse=True)
    return {"message": "Score submitted", "entry": entry}

@app.get("/replay/{session_id}")
def get_replay(session_id: str):
    replay = episode_replays.get(session_id, [])
    if not replay:
        return {"message": "No replay available for this session"}
    return {
        "session_id": session_id,
        "total_steps": len(replay),
        "replay": replay
    }

@app.get("/stats")
def get_stats():
    return {
        "total_episodes": environment_stats["total_episodes"],
        "total_steps": environment_stats["total_steps"],
        "total_approved": environment_stats["total_approved"],
        "total_rejected": environment_stats["total_rejected"],
        "total_escalated": environment_stats["total_escalated"],
        "total_fraud_detected": environment_stats["total_fraud_detected"],
        "avg_reward": round(environment_stats["avg_reward"], 3),
        "approval_rate": round(
            environment_stats["total_approved"] /
            max(environment_stats["total_episodes"], 1), 3
        ),
        "fraud_detection_rate": round(
            environment_stats["total_fraud_detected"] /
            max(environment_stats["total_steps"], 1), 3
        )
    }

@app.get("/scenarios/filter")
def filter_scenarios(tag: str = None, difficulty: str = None):
    from environment.scenarios import ScenarioGenerator
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
                "description": s["description"]
            }
            for s in filtered
        ]
    }

@app.get("/leaderboard")
def get_leaderboard():
    return {
        "leaderboard": leaderboard[:10],
        "total_entries": len(leaderboard)
    }

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    env = get_or_create_env(session_id)
    episode_histories[session_id] = []
    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
            command = message.get("command")
            if command == "reset":
                obs = env.reset(
                    scenario_id=message.get("scenario_id"),
                    difficulty=message.get("difficulty")
                )
                await websocket.send_text(json.dumps({
                    "type": "observation",
                    "data": obs.dict()
                }, default=str))
            elif command == "step":
                action_data = message.get("action")
                action = ClaimAction(**action_data)
                obs, reward, done, info = env.step(action)
                await websocket.send_text(json.dumps({
                    "type": "step_result",
                    "observation": obs.dict(),
                    "reward": reward,
                    "done": done,
                    "info": info
                }, default=str))
            elif command == "state":
                await websocket.send_text(json.dumps({
                    "type": "state",
                    "data": env.state()
                }, default=str))
            elif command == "schema":
                await websocket.send_text(json.dumps({
                    "type": "schema",
                    "data": schema()
                }))
    except WebSocketDisconnect:
        if session_id in environments:
            del environments[session_id]

def main():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()