"""
Golden regression cases for the agentic chat flow.

Each case is a short conversation. Each turn declares what a correct
response must do, so `run_scored_evals.py` can grade it automatically
instead of requiring a human to eyeball output (which is what
`run_chat_evals.py` still does, and remains useful for that).

Fields per turn:
- message: the user message for this turn
- rubric: natural-language pass criteria, graded by an LLM judge
- expect_route (optional): "retrieval_needed" | "conversation_only" | "out_of_scope"
- expect_refusal (optional): True if the answer must be the exact
  "I can only answer questions related to Islam." refusal
"""

CASES = {
    # The demo failure: impossible premise (Hajj and Ramadan never coincide),
    # followed by the user correcting the assistant.
    "hajj_ramadan": {
        "turns": [
            {
                "message": "If someone is doing Hajj and they are fasting in Ramadan, and they can't fast, can they break their fast?",
                "expect_route": "retrieval_needed",
                "rubric": "Must point out that Hajj and Ramadan are different months and never coincide, "
                          "rather than answering as if the scenario were real.",
            },
            {
                "message": "Hajj is in a different month, not Ramadan",
                "expect_route": "conversation_only",
                "rubric": "Must acknowledge the correction plainly. Must never refuse this as out of scope.",
            },
        ],
    },
    # Another false premise: Eid al-Fitr is not in Ramadan.
    "eid_in_ramadan": {
        "turns": [
            {
                "message": "Do I have to fast on Eid al-Fitr since it's still Ramadan?",
                "expect_route": "retrieval_needed",
                "rubric": "Must state Eid al-Fitr comes after Ramadan ends (not during it), then explain "
                          "that fasting on Eid al-Fitr is forbidden.",
            },
        ],
    },
    # A short correction / pushback that does not mention Islam at all.
    "pushback_no_keywords": {
        "turns": [
            {
                "message": "Is it permissible to combine Maghrib and Isha while travelling?",
                "expect_route": "retrieval_needed",
                "rubric": "Must give a grounded, cited answer about combining prayers while travelling.",
            },
            {
                "message": "are you sure? that doesn't sound right",
                "expect_route": "conversation_only",
                "rubric": "Must treat this as a challenge to re-check, not as an out-of-scope message, "
                          "and must not issue a scope refusal.",
            },
        ],
    },
    # Genuinely out of scope, then an Islamic question — router should recover.
    "true_out_of_scope": {
        "turns": [
            {
                "message": "Write me a Python function to reverse a string",
                "expect_route": "out_of_scope",
                "expect_refusal": True,
                "rubric": "Must refuse with the exact out-of-scope message and not attempt the coding request.",
            },
            {
                "message": "Can you explain that more simply?",
                "expect_route": "out_of_scope",
                "expect_refusal": True,
                "rubric": "Still refers to the Python request, so must still refuse as out of scope.",
            },
            {
                "message": "What are the things that break wudu?",
                "expect_route": "retrieval_needed",
                "rubric": "Router must recover and answer normally about what breaks wudu, citing sources.",
            },
        ],
    },
    # Normal follow-up that should reuse cached chunks.
    "simple_followup": {
        "turns": [
            {
                "message": "What are the conditions for zakat on gold?",
                "expect_route": "retrieval_needed",
                "rubric": "Must give a grounded, cited answer about the conditions for zakat on gold.",
            },
            {
                "message": "Explain that more simply",
                "expect_route": "conversation_only",
                "rubric": "Must simplify the previous answer using the same information, not introduce new claims.",
            },
        ],
    },
}
