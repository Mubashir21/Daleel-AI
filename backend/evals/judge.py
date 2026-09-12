"""
LLM-judge grading for a single turn of the agentic chat flow.

Given the question, the source passages the assistant actually had, the
assistant's answer, and a rubric describing what a correct answer must do,
asks a separate model to grade two things independently:

- faithful: the answer doesn't state a ruling, evidence, or claim that goes
  beyond or contradicts the given source passages.
- meets_rubric: the answer satisfies the turn's specific pass criteria.
"""
import json
import logging
from openai import OpenAI
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

JUDGE_SYSTEM_PROMPT = """
You are grading one turn of an Islamic Q&A assistant's response for a regression test suite.

You will be given:
- The user's question for this turn
- The source passages the assistant was given to answer from (may be empty)
- The assistant's actual answer
- A rubric describing what a correct answer for this specific turn must do

Read the ENTIRE answer carefully before deciding anything — the relevant sentence is often the
first one, not something buried later. Do not skim.

Grade two things independently. For each one, first quote the exact sentence(s) from the
assistant's answer that are most relevant to the grade (or state "no such sentence exists" if
none is), then give your verdict based only on that evidence:

1. "faithful": Does the answer avoid stating a ruling, evidence, or claim that goes beyond or
   contradicts the given source passages? An answer that says it could not find an answer, or
   that corrects a false premise using only well-established Islamic facts (the calendar, the
   five pillars, basic term meanings), is faithful even if it cites no source for that part.
   Mark unfaithful only if it invents or misrepresents something the sources do not support.
2. "meets_rubric": Does the answer satisfy the rubric? Check the rubric's requirements one by one
   against the quoted evidence before deciding.

Respond with strict JSON only, no markdown, in this exact shape:
{"faithful": true, "faithful_evidence": "<quoted sentence(s) or 'no such sentence exists'>", "faithful_reason": "...", "meets_rubric": true, "rubric_evidence": "<quoted sentence(s) or 'no such sentence exists'>", "rubric_reason": "..."}
""".strip()


def judge_turn(question: str, answer: str, sources_text: str, rubric: str) -> dict:
    user_prompt = f"""
Question: {question}

Rubric for this turn: {rubric}

Source passages given to the assistant:
{sources_text or "(none provided)"}

Assistant's answer:
{answer}
""".strip()

    try:
        response = client.chat.completions.create(
            model=settings.eval_judge_model,
            messages=[
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )
        result = json.loads(response.choices[0].message.content)
        result.setdefault("faithful", False)
        result.setdefault("meets_rubric", False)
        return result
    except Exception as e:
        logger.error(f"Judge call failed: {e}")
        return {
            "faithful": False,
            "faithful_reason": f"judge error: {e}",
            "meets_rubric": False,
            "rubric_reason": f"judge error: {e}",
        }
