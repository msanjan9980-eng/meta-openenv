"""
Interactive demo for the insurance claim environment.

Uses stateful HTTP ``/episode/reset`` and ``/episode/step`` so multi-step
episodes work without WebSockets. Set ``BASE_URL`` to your server root.
"""

import os

import requests

BASE_URL = os.environ.get("BASE_URL", "http://localhost:8000").rstrip("/")
SESSION_ID = os.environ.get("DEMO_SESSION_ID", "demo")


def print_separator() -> None:
    print("\n" + "=" * 60 + "\n")


def print_claim(claim_data: dict) -> None:
    print("CLAIM DETAILS:")
    print(f"  Type      : {claim_data['claim']['claim_type'].upper()}")
    print(f"  Amount    : ${claim_data['claim']['amount']:,.2f}")
    print(f"  Severity  : {claim_data['claim']['severity']}")
    print(f"  Description: {claim_data['claim']['description']}")
    print()
    print("POLICY INFO:")
    claim_type = claim_data["claim"]["claim_type"]
    limit = claim_data["policy"]["coverage_limits"].get(claim_type, 0)
    deductible = claim_data["policy"]["deductibles"].get(claim_type, 0)
    print(f"  Coverage Limit : ${limit:,.2f}")
    print(f"  Deductible     : ${deductible:,.2f}")
    print(f"  Excluded       : {claim_data['policy']['excluded_conditions'] or 'None'}")
    print(f"  Required Docs  : {', '.join(claim_data['policy']['required_documents'])}")
    print()
    print("USER HISTORY:")
    user = claim_data["user_history"]
    print(f"  Total Claims   : {user['total_claims']}")
    print(f"  Total Payout   : ${user['total_payout']:,.2f}")
    print(f"  Risk Score     : {user['risk_score']}")
    print(f"  Claim Frequency: {user['claim_frequency']} per year")
    print(f"  Flagged Before : {user['flagged_previous']}")
    print(f"  Account Age    : {user['account_age_days']} days")
    print()
    print("DOCUMENTS:")
    for doc_name, doc_info in claim_data["documents"].items():
        status = str(doc_info["status"]).upper()
        emoji = "✓" if status == "VERIFIED" else "?" if status == "UPLOADED" else "✗"
        print(f"  {emoji} {doc_name}: {status}")
    print()
    if claim_data.get("policy_violations"):
        print("POLICY VIOLATIONS DETECTED:")
        for v in claim_data["policy_violations"]:
            print(f"  ! {v}")
        print()
    if claim_data.get("risk_signals"):
        print("RISK SIGNALS:")
        for s in claim_data["risk_signals"]:
            print(f"  ! {s['signal_type']}: {s['description']}")
        print()


def get_user_action() -> str:
    print("AVAILABLE ACTIONS:")
    actions = [
        ("1", "analyze_claim", "Examine claim details more closely"),
        ("2", "detect_fraud_signals", "Run fraud detection"),
        ("3", "approve_claim", "Approve the claim"),
        ("4", "reject_claim", "Reject the claim"),
        ("5", "escalate_claim", "Escalate for manual review"),
        ("6", "request_additional_info", "Request missing documents"),
        ("7", "ignore", "Skip (penalized)"),
    ]
    for num, action, desc in actions:
        print(f"  {num}. {action} - {desc}")

    while True:
        choice = input("\nEnter your choice (1-7): ").strip()
        if choice in [str(i) for i in range(1, 8)]:
            return actions[int(choice) - 1][1]
        print("Invalid choice. Please enter 1-7.")


def get_user_reasoning(action: str) -> dict:
    print("\nNow provide your reasoning:")

    policy_violation = input("  Policy violation detected? (y/n): ").strip().lower() == "y"
    claim_amount_valid = input("  Claim amount valid? (y/n): ").strip().lower() == "y"
    user_risk_high = input("  User risk high? (y/n): ").strip().lower() == "y"
    documents_complete = input("  Documents complete? (y/n): ").strip().lower() == "y"

    fraud_input = input("  Any fraud indicators? (comma separated or leave blank): ").strip()
    fraud_indicators = [f.strip() for f in fraud_input.split(",")] if fraud_input else []

    confidence = float(input("  Your confidence (0.0 to 1.0): ").strip())

    return {
        "policy_violation": policy_violation,
        "claim_amount_valid": claim_amount_valid,
        "user_risk_high": user_risk_high,
        "documents_complete": documents_complete,
        "fraud_indicators": fraud_indicators,
        "confidence": confidence,
        "recommendation": action,
    }


def play_episode(difficulty: str) -> None:
    print_separator()
    print(f"Starting new episode with difficulty: {difficulty.upper()}")
    print_separator()

    response = requests.post(
        f"{BASE_URL}/episode/reset",
        json={"difficulty": difficulty, "session_id": SESSION_ID},
        timeout=60,
    )

    if response.status_code != 200:
        print(f"Error resetting environment: {response.text}")
        return

    claim_data = response.json()
    step = 0
    total_reward = 0.0
    done = False

    while not done:
        step += 1
        print(f"\n{'=' * 60}")
        print(f"STEP {step}")
        print(f"{'=' * 60}")

        print_claim(claim_data)

        action = get_user_action()
        reasoning = get_user_reasoning(action)

        response = requests.post(
            f"{BASE_URL}/episode/step",
            json={
                "action": {
                    "action": action,
                    "reasoning": reasoning,
                    "parameters": {},
                    "metadata": {},
                },
                "session_id": SESSION_ID,
            },
            timeout=60,
        )

        if response.status_code != 200:
            print(f"Error: {response.text}")
            break

        result = response.json()
        reward = float(result.get("reward") or 0.0)
        done = bool(result["done"])
        claim_data = result["observation"]
        info = result["info"]

        total_reward += reward

        print(f"\nREWARD FOR THIS STEP: {reward:.3f}")
        print(f"DONE: {done}")

        if done:
            print_separator()
            print("EPISODE COMPLETE!")
            print(f"\nFINAL RESULTS:")
            print(f"  Total Steps    : {step}")
            print(f"  Total Reward   : {total_reward:.3f}")
            print(f"  Average Reward : {total_reward / step:.3f}")
            print(f"\nREWARD BREAKDOWN:")
            components = info["reward_components"]
            print(f"  Decision Accuracy : {components['decision']:.3f}")
            print(f"  Fraud Detection   : {components['fraud_detection']:.3f}")
            print(f"  Reasoning Quality : {components['reasoning']:.3f}")
            print(f"  Efficiency        : {components['efficiency']:.3f}")
            print(f"\nGROUND TRUTH:")
            gt = info["ground_truth"]
            print(f"  Correct Action    : {gt['correct_action']}")
            print(f"  Was Fraud         : {gt['fraud_label']}")
            print(f"  Policy Violation  : {gt['has_policy_violation']}")
            print_separator()


def main() -> None:
    print("=" * 60)
    print("  INSURANCE CLAIM VALIDATION - INTERACTIVE DEMO")
    print("=" * 60)
    print("\nWelcome! You will evaluate insurance claims and make decisions.")
    print("Your goal is to correctly approve, reject, or escalate claims.")
    print("You will be scored on accuracy, fraud detection, and efficiency.")
    print(f"\nServer: {BASE_URL} (session `{SESSION_ID}`)")

    while True:
        print("\nChoose difficulty:")
        print("  1. Easy")
        print("  2. Medium")
        print("  3. Hard")
        print("  4. Quit")

        choice = input("\nEnter choice (1-4): ").strip()

        if choice == "1":
            play_episode("easy")
        elif choice == "2":
            play_episode("medium")
        elif choice == "3":
            play_episode("hard")
        elif choice == "4":
            print("\nThanks for playing!")
            break
        else:
            print("Invalid choice.")

        again = input("\nPlay another episode? (y/n): ").strip().lower()
        if again != "y":
            print("\nThanks for playing!")
            break


if __name__ == "__main__":
    main()
