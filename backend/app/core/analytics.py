import logging
from posthog import Posthog
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

posthog = Posthog(
    settings.posthog_api_key,
    host="https://us.i.posthog.com",
)

posthog.disabled = not bool(settings.posthog_api_key)

# Pricing per million tokens (input, output)
MODEL_PRICING = {
    "gpt-5.6-sol":  (4.00, 20.00),
    "gpt-5.6-terra": (2.00, 12.00),
    "gpt-5.6-luna": (0.20,  1.20),
    "gpt-5.5":      (5.00, 30.00),
    "gpt-5.4":      (2.50, 15.00),
    "gpt-5.4-mini": (0.75,  4.50),
    "gpt-4.1":      (2.00,  8.00),
    "gpt-4.1-mini": (0.40,  1.60),
    "gpt-4o":       (2.50, 10.00),
    "gpt-4o-mini":  (0.15,  0.60),
}


def calculate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    prices = MODEL_PRICING.get(model, (0, 0))
    return round((input_tokens * prices[0] + output_tokens * prices[1]) / 1_000_000, 6)


def capture_chat(
    session_id: str,
    route: str,
    question: str,
    answer: str,
    model: str,
    latency: float,
    retrieval_used: bool,
    input_tokens: int = 0,
    output_tokens: int = 0,
    retrieval_latency: float | None = None,
    total_latency: float | None = None,
):
    if not settings.posthog_api_key:
        return

    total_cost = calculate_cost(model, input_tokens, output_tokens)

    try:
        posthog.capture(
            distinct_id=session_id,
            event="$ai_generation",
            properties={
                "$ai_model": model,
                "$ai_provider": "openai",
                "$ai_input": [{"role": "user", "content": question}],
                "$ai_output_choices": [{"message": {"content": answer}}],
                "$ai_latency": latency,
                "$ai_input_tokens": input_tokens,
                "$ai_output_tokens": output_tokens,
                "$ai_total_cost_usd": total_cost,
                "$ai_trace_id": session_id,
                "route": route,
                "retrieval_used": retrieval_used,
                "retrieval_latency": retrieval_latency,
                "total_latency": total_latency,
                "app": "daleel-ai",
            },
        )
    except Exception as e:
        logger.warning(f"Failed to capture analytics: {e}")
