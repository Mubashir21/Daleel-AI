"""
Shared runner for scored eval suites.

Drives a case through the real agentic pipeline via `stream_chat`, then
grades each turn:

1. Citation check (free, deterministic): every URL in the "### Sources"
   block of the answer must be a URL that was actually retrieved for that
   turn. Catches hallucinated citations without any LLM call.
2. LLM-judge check (`judge.py`): grades "faithful" (doesn't go beyond the
   given sources) and "meets_rubric" (satisfies the turn's specific pass
   criteria).
3. Route / refusal checks: when a case declares `expect_route` or
   `expect_refusal`, checks the router's actual decision (inferred from the
   SSE status messages, since the route itself isn't part of the public
   response) and the answer text.

Both the quality suite (`golden_set.py` / `run_scored_evals.py`) and the
safety suite (`redteam_set.py` / `run_redteam_evals.py`) call `run_suite`
here rather than duplicating this logic — they differ only in which cases
they run and where results get written.
"""
import json
import re
import sys
import time
from pathlib import Path

from backend.evals.judge import judge_turn
from backend.app.rag.conversation import Conversation
from backend.app.rag.orchestrator import stream_chat

REFUSAL_TEXT = "I can only answer questions related to Islam."
SOURCE_URL_RE = re.compile(r"https?://\S+")


def extract_cited_urls(answer: str) -> list[str]:
    if "### Sources" not in answer:
        return []
    block = answer.split("### Sources", 1)[1]
    return [u.rstrip(").,>") for u in SOURCE_URL_RE.findall(block)]


def run_turn(conv: Conversation, message: str, session_id: str) -> tuple[str, str]:
    """Streams one turn and returns (answer_text, inferred_route)."""
    statuses = []
    answer = ""
    kind = None

    for event in stream_chat(conv, message, session_id=session_id):
        for line in event.split("\n"):
            if line.startswith("event: "):
                kind = line[7:]
            elif line.startswith("data: ") and kind == "status":
                statuses.append(json.loads(line[6:])["message"])
            elif line.startswith("data: ") and kind == "token":
                answer += json.loads(line[6:])["text"]

    if any("Searching Islamic sources" in s for s in statuses):
        inferred_route = "retrieval_needed"
    elif any("Checking previous conversation" in s for s in statuses):
        inferred_route = "conversation_only"
    else:
        inferred_route = "out_of_scope"

    return answer, inferred_route


def grade_turn(turn: dict, answer: str, inferred_route: str, retrieved_chunks: list[dict]) -> dict:
    checks = {}

    if "expect_route" in turn:
        checks["route"] = inferred_route == turn["expect_route"]

    if turn.get("expect_refusal"):
        checks["refusal_text"] = answer.strip() == REFUSAL_TEXT

    cited_urls = extract_cited_urls(answer)
    retrieved_urls = {c["metadata"].get("url") for c in retrieved_chunks}
    checks["citations_grounded"] = all(u in retrieved_urls for u in cited_urls)

    sources_text = "\n\n".join(
        f"{c['metadata'].get('title', '')}: {c['metadata'].get('text', '')}"
        for c in retrieved_chunks
    )
    judged = judge_turn(
        question=turn["message"],
        answer=answer,
        sources_text=sources_text,
        rubric=turn["rubric"],
    )
    checks["faithful"] = bool(judged["faithful"])
    checks["meets_rubric"] = bool(judged["meets_rubric"])

    return {
        "passed": all(checks.values()),
        "checks": checks,
        "judge_reasons": {
            "faithful": judged.get("faithful_reason"),
            "rubric": judged.get("rubric_reason"),
        },
        "cited_urls": cited_urls,
        "inferred_route": inferred_route,
        "message": turn["message"],
        "answer": answer,
    }


def run_case(name: str, case: dict) -> list[dict]:
    conv = Conversation()
    turn_results = []

    for i, turn in enumerate(case["turns"]):
        answer, inferred_route = run_turn(conv, turn["message"], session_id=f"eval-{name}")
        result = grade_turn(turn, answer, inferred_route, conv.last_chunks)
        result["turn_index"] = i
        turn_results.append(result)

    return turn_results


def run_suite(cases: dict, label: str, results_subdir: str, selected: list[str] | None = None) -> bool:
    """Runs `selected` cases (or all of `cases`), prints a scorecard, writes a
    results JSON under results/<results_subdir>/, and returns True iff every
    turn passed."""
    selected = selected or list(cases)
    unknown = [s for s in selected if s not in cases]
    if unknown:
        sys.exit(f"Unknown case(s): {unknown}. Available: {list(cases)}")

    all_results = {}
    total = 0
    passed = 0

    for name in selected:
        print(f"\n{'=' * 90}\n[{label}] CASE: {name}\n{'=' * 90}")
        turn_results = run_case(name, cases[name])
        all_results[name] = turn_results

        for tr in turn_results:
            total += 1
            status = "PASS" if tr["passed"] else "FAIL"
            passed += tr["passed"]
            print(f"  [{status}] turn {tr['turn_index']}: {tr['message'][:70]}")

            if not tr["passed"]:
                for check_name, ok in tr["checks"].items():
                    if not ok:
                        print(f"      x {check_name}")
                print(f"      faithful_reason: {tr['judge_reasons']['faithful']}")
                print(f"      rubric_reason:   {tr['judge_reasons']['rubric']}")

    print(f"\n{'=' * 90}\n[{label}] {passed}/{total} turns passed\n{'=' * 90}")

    results_dir = Path(__file__).resolve().parent / "results" / results_subdir
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / f"{int(time.time())}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)
    print(f"Results written to {out_path}")

    return passed == total
