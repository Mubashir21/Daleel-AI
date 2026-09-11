"""
Automated, scored red-team evals for the agentic chat flow — safety suite.

Runs every case in `redteam_set.py` (jailbreaks, prompt injection, prompt
leak probes, hallucination bait, scope erosion, harm-adjacent requests)
through the real pipeline and grades each turn the same way as the quality
suite — see `runner.py` for the shared grading logic and
`run_scored_evals.py` for the quality suite this pairs with.

A failure here means the bot broke one of its own rules, not that it gave a
mediocre answer — treat any failure as a "do not ship" signal, not a
nice-to-fix.

Exits with code 1 if any turn fails, so this can be wired into CI later.

Usage (from repo root, with .env configured):
    python backend/evals/run_redteam_evals.py                        # all cases
    python backend/evals/run_redteam_evals.py jailbreak_roleplay_persona

Each run costs real API calls (retrieval + generation + judge). Analytics
are disabled for eval runs. Results are written to
backend/evals/results/safety/.
"""
import io
import logging
import os
import sys
from pathlib import Path

# Make `backend.app...` importable and keep PostHog quiet
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
os.environ.setdefault("POSTHOG_API_KEY", "")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

logging.basicConfig(level=logging.WARNING)

from backend.evals.redteam_set import CASES  # noqa: E402
from backend.evals.runner import run_suite  # noqa: E402


if __name__ == "__main__":
    ok = run_suite(
        CASES,
        label="SAFETY",
        results_subdir="safety",
        selected=sys.argv[1:] or None,
    )
    sys.exit(0 if ok else 1)
