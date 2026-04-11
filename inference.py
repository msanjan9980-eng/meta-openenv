import asyncio
import os
import json
import re
import textwrap
from typing import Any, Dict, List, Optional
from openai import OpenAI

API_KEY = os.getenv("HF_TOKEN") or os.getenv("API_KEY") or "nokey"
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
BENCHMARK = os.getenv("INSURANCE_ENV_BENCHMARK", "insurance-claim-validation")
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "https://sanjan-m-insurance-claim-validation.hf.space")

MAX_STEPS = 6
TEMPERATURE = 0.3
MAX_TOKENS = 300
MAX_REWARD_PER_STEP = 1.0
MAX_TOTAL_REWARD = MAX_STEPS * MAX_REWARD_PER_STEP
SUCCESS_SCORE_THRESHOLD = 0.4

TASKS = [
    {
        "name": "easy_claim_validation",
        "difficulty": "easy",
        "system_prompt": (
            "You are an AI insurance claims adjuster. "
            "Each turn respond with a JSON object only: "
            '{"decision": "approve|deny|request_info|escalate", '
            '"confidence": 0.0-1.0, "reasoning": "short explanation", "flags": []}. '
            "No preamble, no markdown."
        ),
    },
    {
        "name": "medium_fraud_detection",
        "difficulty": "medium",
        "system_prompt": (
            "You are an insurance fraud investigator. "
            "Respond with JSON only: "
            '{"decision": "approve|deny|request_info|escalate", '
            '"confidence": 0.0-1.0, "reasoning": "explanation", "flags": ["fraud_pattern_if_any"]}. '
            "No preamble, no markdown."
        ),
    },
    {
        "name": "hard_complex_multi_party",
        "difficulty": "hard",
        "system_prompt": (
            "You are a senior insurance specialist on complex multi-party claims. "
            "Respond with JSON only: "
            '{"decision": "approve|deny|request_info|escalate", '
            '"confidence": 0.0-1.0, "reasoning": "thorough reasoning", "flags": []}. '
            "No preamble, no markdown."
        ),
    },
]


def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)


def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str] = None) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}", flush=True)


def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)


DECISION_MAP = {
    "approve": "approve_claim",
    "deny": "reject_claim",
    "reject": "reject_claim",
    "request_info": "request_additional_info",
    "escalate": "escalate_claim",
    "analyze": "analyze_claim",
    "detect_fraud": "detect_fraud_signals",
}

def parse_action(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        parsed = json.loads(cleaned)
    except Exception:
        parsed = {}
    decision = parsed.get("decision", "request_info")
    action = DECISION_MAP.get(decision, "request_additional_info")
    confidence = float(parsed.get("confidence", 0.5))
    flags = list(parsed.get("flags", []))
    reasoning_text = parsed.get("reasoning", raw[:200])
    if isinstance(reasoning_text, dict):
        reasoning_text = str(reasoning_text)
    return {
        "action": action,
        "reasoning": {
            "policy_violation": any(f in ["policy_violation", "coverage_exceeded"] for f in flags),
            "claim_amount_valid": True,
            "user_risk_high": any(f in ["high_risk", "multiple_recent_claims", "flagged_user"] for f in flags),
            "documents_complete": action == "approve_claim",
            "fraud_indicators": flags,
            "confidence": confidence,
            "recommendation": reasoning_text[:500] if reasoning_text else None,
        },
        "metadata": {},
        "parameters": {},
    }


def get_model_action(
    client: OpenAI,
    task: Dict,
    step: int,
    obs: Dict,
    last_reward: float,
    history: List[str],
) -> str:
    history_block = "\n".join(history[-4:]) if history else "None"
    user_prompt = (
        f"Step: {step}\n"
        f"Last reward: {last_reward:.2f}\n"
        f"Claim data: {json.dumps(obs.get('claim', obs))}\n"
        f"Documents: {json.dumps(obs.get('documents', {}))}\n"
        f"Risk signals: {obs.get('risk_signals', [])}\n"
        f"Previous steps:\n{history_block}\n"
        f"Provide your JSON decision."
    )
    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": task["system_prompt"]},
                {"role": "user", "content": user_prompt},
            ],
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
            stream=False,
        )
        return (completion.choices[0].message.content or "").strip()
    except Exception as exc:
        print(f"[DEBUG] Model error: {exc}", flush=True)
        return '{"decision": "request_info", "confidence": 0.5, "reasoning": "API error", "flags": []}'


async def run_task(client: OpenAI, task: Dict) -> float:
    import httpx
    task_name = task["name"]
    log_start(task=task_name, env=BENCHMARK, model=MODEL_NAME)
    rewards: List[float] = []
    history: List[str] = []
    steps_taken = 0
    score = 0.0
    success = False
    try:
        async with httpx.AsyncClient(base_url=ENV_BASE_URL, timeout=30) as http:
            r = await http.post("/reset", json={"difficulty": task["difficulty"]})
            result = r.json()
            obs = result.get("observation", result)
            last_reward = 0.0
            for step in range(1, MAX_STEPS + 1):
                if result.get("done", False):
                    break
                raw = get_model_action(client, task, step, obs, last_reward, history)
                action_dict = parse_action(raw)
                try:
                    sr = await http.post("/step", json={"action": action_dict})
                    result = sr.json()
                    obs = result.get("observation", result)
                    reward = float(result.get("reward") or 0.0)
                    done = bool(result.get("done", False))
                    error = None
                except Exception as se:
                    reward = 0.0
                    done = False
                    error = str(se)[:80]
                rewards.append(reward)
                steps_taken = step
                last_reward = reward
                history.append(f"Step {step}: {action_dict.get('decision')} -> reward {reward:.2f}")
                log_step(step=step, action=str(action_dict), reward=reward, done=done, error=error)
                if done:
                    break
        total = sum(rewards)
        raw_score = total / MAX_TOTAL_REWARD if MAX_TOTAL_REWARD > 0 else 0.5
        score = max(0.001, min(0.999, raw_score))
        success = score >= SUCCESS_SCORE_THRESHOLD
    except Exception as exc:
        print(f"[DEBUG] Episode error: {exc}", flush=True)
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)
    return score


async def main() -> None:
    client = OpenAI(base_url=API_BASE_URL, api_key=API_KEY)
    scores: List[float] = []
    for task in TASKS:
        print(f"\n{'='*50}", flush=True)
        print(f"Task: {task['name']} ({task['difficulty']})", flush=True)
        print(f"{'='*50}", flush=True)
        score = await run_task(client, task)
        scores.append(score)
        print(f"Score: {score:.3f}", flush=True)
    avg = sum(scores) / len(scores) if scores else 0.0
    print(f"\nFINAL: easy={scores[0]:.3f} medium={scores[1]:.3f} hard={scores[2]:.3f} avg={avg:.3f}", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
