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

def get_or_create_env(session_id: str) -> InsuranceClaimEnvironment:
    if session_id not in environments:
        environments[session_id] = InsuranceClaimEnvironment({"max_steps": 6})
    return environments[session_id]

@app.get("/")
def root():
    return {
        "name": "Insurance Claim Validation Environment",
        "version": "2.0.0",
        "description": "OpenEnv-compatible RL environment for insurance claim validation",
        "endpoints": {
            "POST /reset": "Reset environment and get initial observation",
            "POST /step": "Take a step with a ClaimAction",
            "GET /state": "Get current environment state",
            "GET /schema": "Get action and observation schemas",
            "GET /health": "Health check",
            "GET /scenarios": "List all available scenarios",
            "GET /metrics": "Get environment metrics",
            "WS /ws/{session_id}": "WebSocket for real-time interaction"
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
    episode_histories[session_id].append({
        "action": request.action.dict(),
        "reward": reward,
        "done": done
    })
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