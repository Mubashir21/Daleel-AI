import cohere
import logging
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

co = cohere.ClientV2(api_key=settings.cohere_api_key)


def build_rerank_document(match):
    meta = match["metadata"]

    return f"""
Title: {meta.get("title", "")}

Question: {meta.get("question", "")}

Content:
{meta.get("text", "")}
""".strip()


def rerank_matches(query, matches, top_n=5):
    if not matches:
        return []

    documents = [build_rerank_document(match) for match in matches]

    try:
        response = co.rerank(
            model=settings.rerank_model,
            query=query,
            documents=documents,
            top_n=top_n,
            # Cohere latency is spiky (trial keys especially). Don't let one slow or
            # rate-limited call stall the whole answer: fail fast and fall back.
            request_options={
                "timeout_in_seconds": settings.rerank_timeout,
                "max_retries": 0,
            },
        )
    except Exception as e:
        logger.warning(
            f"Rerank failed ({type(e).__name__}: {e}); falling back to hybrid search order"
        )
        fallback = matches[:top_n]
        for match in fallback:
            match["rerank_score"] = None
            match["pinecone_score"] = match.get("score", 0)
        return fallback

    reranked = []

    for result in response.results:
        original_match = matches[result.index]

        original_match["rerank_score"] = result.relevance_score
        original_match["pinecone_score"] = original_match.get("score", 0)

        reranked.append(original_match)
    return reranked