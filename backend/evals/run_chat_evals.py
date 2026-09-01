"""
Manual regression evals for the agentic chat flow.

Runs multi-turn conversations through the real pipeline (router → retrieval →
generation) and prints the route, retrieved sources and answer for each turn so
you can eyeball behaviour on tricky inputs (false premises, corrections,
follow-ups, out-of-scope).

Usage (from repo root, with .env configured):
    python backend/evals/run_chat_evals.py              # run all cases
    python backend/evals/run_chat_evals.py hajj_ramadan # run one case

Each run costs real API calls. Analytics are disabled for eval runs.
"""
import io
import json
import logging
import os
import sys
from pathlib import Path

# Make `backend.app...` importable and keep PostHog quiet
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("POSTHOG_API_KEY", "")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from backend.app.rag.conversation import Conversation  # noqa: E402
from backend.app.rag.orchestrator import stream_chat  # noqa: E402


CASES = {
    # The demo failure: impossible premise (Hajj and Ramadan never coincide),
    # followed by the user correcting the assistant.
    "hajj_ramadan": {
        "expect": "Turn 1 should point out Hajj and Ramadan are different months, "
                  "not answer 'yes'. Turn 2 must acknowledge, never refuse as out of scope.",
        "turns": [
            "If someone is doing Hajj and they are fasting in Ramadan, and they can't fast, can they break their fast?",
            "Hajj is in a different month, not Ramadan",
        ],
    },
    # Another false premise: Eid al-Fitr is not in Ramadan.
    "eid_in_ramadan": {
        "expect": "Should say Eid al-Fitr comes after Ramadan ends, then explain fasting on Eid is forbidden.",
        "turns": [
            "Do I have to fast on Eid al-Fitr since it's still Ramadan?",
        ],
    },
    # A short correction / pushback that does not mention Islam at all.
    "pushback_no_keywords": {
        "expect": "Turn 2 is a challenge, not out of scope. Should re-check against the sources.",
        "turns": [
            "Is it permissible to combine Maghrib and Isha while travelling?",
            "are you sure? that doesn't sound right",
        ],
    },
    # Genuinely out of scope, then an Islamic question — router should recover.
    "true_out_of_scope": {
        "expect": "Turns 1-2 refused (the follow-up still refers to the Python request). "
                  "Turn 3 answered normally — router recovers after out-of-scope turns.",
        "turns": [
            "Write me a Python function to reverse a string",
            "Can you explain that more simply?",
            "What are the things that break wudu?",
        ],
    },
    # Normal follow-up that should reuse cached chunks.
    "simple_followup": {
        "expect": "Turn 2 routes conversation_only and simplifies the previous answer.",
        "turns": [
            "What are the conditions for zakat on gold?",
            "Explain that more simply",
        ],
    },
}


def run_case(name: str, case: dict):
    print("\n" + "#" * 90)
    print(f"# CASE: {name}")
    print(f"# EXPECT: {case['expect']}")
    print("#" * 90)

    conv = Conversation()
    for turn in case["turns"]:
        print("\n" + "=" * 90)
        print(f"USER: {turn}")
        print("-" * 90)

        answer = ""
        kind = None
        for event in stream_chat(conv, turn, session_id=f"eval-{name}"):
            for line in event.split("\n"):
                if line.startswith("event: "):
                    kind = line[7:]
                elif line.startswith("data: ") and kind == "status":
                    print(f"  [status] {json.loads(line[6:])['message']}")
                elif line.startswith("data: ") and kind == "token":
                    answer += json.loads(line[6:])["text"]

        print("-" * 90)
        print(f"ASSISTANT:\n{answer}")

        if conv.last_chunks:
            print("\n[cached sources]")
            seen = set()
            for c in conv.last_chunks:
                url = c["metadata"].get("url")
                if url not in seen:
                    seen.add(url)
                    print(f"  - {c['metadata'].get('title')} | {url}")


if __name__ == "__main__":
    selected = sys.argv[1:] or list(CASES)
    unknown = [s for s in selected if s not in CASES]
    if unknown:
        sys.exit(f"Unknown case(s): {unknown}. Available: {list(CASES)}")

    for name in selected:
        run_case(name, CASES[name])
