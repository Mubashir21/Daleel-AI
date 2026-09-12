"""
Manual regression evals for the agentic chat flow.

Runs the same cases as `run_scored_evals.py` (defined once in `golden_set.py`)
through the real pipeline (router -> retrieval -> generation) and prints the
route, retrieved sources and answer for each turn so you can eyeball behaviour
on tricky inputs (false premises, corrections, follow-ups, out-of-scope).

For automated pass/fail scoring (citation grounding + LLM-judge faithfulness
and rubric checks), use `run_scored_evals.py` instead.

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
from backend.evals.golden_set import CASES  # noqa: E402


def run_case(name: str, case: dict):
    print("\n" + "#" * 90)
    print(f"# CASE: {name}")
    print("#" * 90)

    conv = Conversation()
    for turn in case["turns"]:
        print("\n" + "=" * 90)
        print(f"USER: {turn['message']}")
        print(f"EXPECT: {turn['rubric']}")
        print("-" * 90)

        answer = ""
        kind = None
        for event in stream_chat(conv, turn["message"], session_id=f"eval-{name}"):
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
