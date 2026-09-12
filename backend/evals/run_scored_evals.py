"""
Automated, scored regression evals for the agentic chat flow — quality suite.

Runs every case in `golden_set.py` through the real pipeline and grades each
turn (citation grounding, LLM-judge faithfulness + rubric satisfaction,
route/refusal checks). See `runner.py` for the grading logic shared with the
red-team safety suite (`run_redteam_evals.py`).

Exits with code 1 if any turn fails, so this can be wired into CI later.

Usage (from repo root, with .env configured):
    python backend/evals/run_scored_evals.py              # run all cases
    python backend/evals/run_scored_evals.py hajj_ramadan  # run one case

Each run costs real API calls (retrieval + generation + judge). Analytics
are disabled for eval runs. Results are written to
backend/evals/results/quality/.
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

from backend.evals.golden_set import CASES  # noqa: E402
from backend.evals.runner import run_suite  # noqa: E402


if __name__ == "__main__":
    ok = run_suite(
        CASES,
        label="QUALITY",
        results_subdir="quality",
        selected=sys.argv[1:] or None,
    )
    sys.exit(0 if ok else 1)
