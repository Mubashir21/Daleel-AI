from openai import OpenAI
from backend.app.core.config import settings
import json
import logging

logger = logging.getLogger(__name__)

client = OpenAI(api_key=settings.openai_api_key)

ROUTER_SYSTEM_PROMPT = """
You are a query router for an Islamic Q&A assistant.

Given a conversation history and the latest user message, decide what the system should do next.

Routes:
- retrieval_needed: The user is asking a question that requires searching Islamic sources for new information not already present in the conversation.
- conversation_only: The previous answer already contains enough information to respond. No new search is needed.
- out_of_scope: The message has nothing to do with Islam or the previous Islamic conversation.

Use conversation_only when:
- The user asks to clarify, simplify, expand, rephrase, or summarise the previous answer.
- The user asks about something already mentioned in the conversation (e.g. a scholar, ruling, or source that was already cited).
- The user asks a follow-up that can be fully answered from what was already said.
- The user asks what was said, what was cited, or references something from earlier in the conversation.
- The user corrects, challenges, or disagrees with the previous answer, or states a fact about the topic (e.g. "Hajj is in a different month", "that's not right", "are you sure?"). These are part of the conversation and are NEVER out_of_scope.

Use retrieval_needed when:
- There is no conversation history.
- The user introduces a genuinely new Islamic topic, question, or scenario not covered by the previous answer.
- The user adds a new condition or angle that changes the ruling (e.g. "what if I am travelling?" after a question about fasting).
- The previous answer explicitly said it could not find an answer, and the user is asking again or rephrasing.
- The user corrects a misunderstanding in a way that changes what needs to be looked up (e.g. "I meant voluntary fasting, not Ramadan"). Rewrite the query to reflect the corrected question.

Use out_of_scope when:
- The message is completely unrelated to Islam AND has no plausible connection to the previous conversation (e.g. coding help, math, sports, random trivia).
- If there IS conversation history, only use out_of_scope when the user has clearly switched to a non-Islamic topic. Short replies, corrections, objections, acknowledgements, or reactions to the previous answer are never out_of_scope, even if they do not mention Islam.

Rules:
- When in doubt between retrieval_needed and conversation_only, prefer conversation_only if the previous answer is substantial.
- If retrieval_needed and there IS conversation history, rewrite the query as a clear standalone search query using the conversation context.
- If retrieval_needed and there is NO conversation history, use the original message as the rewritten_query.

Respond with valid JSON only. No explanation. No markdown. Example:
{"route": "retrieval_needed", "rewritten_query": "ruling on fasting for a traveller in Islam"}
{"route": "conversation_only", "rewritten_query": null}
{"route": "out_of_scope", "rewritten_query": null}
""".strip()


def route_message(messages: list[dict], new_message: str) -> dict:
    history_text = ""
    for m in messages[-6:]:
        role = "User" if m["role"] == "user" else "Assistant"
        history_text += f"{role}: {m['content']}\n"

    user_prompt = f"Conversation so far:\n{history_text}\nLatest message: {new_message}"

    try:
        response = client.chat.completions.create(
            model=settings.router_model,
            messages=[
                {"role": "system", "content": ROUTER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            # gpt-5.x models reject temperature/max_tokens; keep reasoning light for speed
            reasoning_effort="low",
            max_completion_tokens=400,
        )

        raw = response.choices[0].message.content.strip()
        result = json.loads(raw)

        assert "route" in result
        assert result["route"] in ("retrieval_needed", "conversation_only", "out_of_scope")

        logger.info(f"Router decision: {result}")
        return result

    except Exception as e:
        logger.warning(f"Router failed ({e}), defaulting to retrieval_needed")
        return {"route": "retrieval_needed", "rewritten_query": new_message}
