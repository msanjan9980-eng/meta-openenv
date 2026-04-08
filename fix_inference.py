import re, json

content = open('inference.py', encoding='utf-8').read()

old = '''def parse_action(raw: str) -> Dict[str, Any]:
    cleaned = re.sub(r"```(?:json)?|```", "", raw).strip()
    try:
        parsed = json.loads(cleaned)
        return {
            "decision": parsed.get("decision", "request_info"),
            "confidence": float(parsed.get("confidence", 0.5)),
            "reasoning": str(parsed.get("reasoning", "")),
            "flags": list(parsed.get("flags", [])),
        }
    except Exception:
        return {"decision": "request_info", "confidence": 0.5, "reasoning": raw[:200], "flags": []}'''

new = '''DECISION_MAP = {
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
    }'''

if old in content:
    content = content.replace(old, new)
    open('inference.py', 'w', encoding='utf-8').write(content)
    print("Done - parse_action updated")
else:
    print("FAILED - could not find parse_action to replace")
    print("Current parse_action:")
    start = content.find("def parse_action")
    print(content[start:start+400])