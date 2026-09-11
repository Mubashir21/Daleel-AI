from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from backend.app.schemas.query import QueryRequest, QueryResponse, ChatRequest
from backend.app.rag.generator import generate_answer, stream_answer
from backend.app.rag.orchestrator import stream_chat
from backend.app.core.session_store import get_or_create_session
from backend.app.core.rate_limit import limiter
from backend.app.core.config import settings
import json

router = APIRouter()


@router.post("/query", response_model=QueryResponse)
@limiter.limit(settings.rate_limit)
def query(request: Request, payload: QueryRequest):
    try:
        result = generate_answer(payload.query)

        return QueryResponse(
            answer=result
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate answer: {str(e)}"
        )


@router.post("/query/stream")
@limiter.limit(settings.rate_limit)
def query_stream(request: Request, payload: QueryRequest):
    try:
        return StreamingResponse(
            stream_answer(payload.query),
            media_type="text/event-stream"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate streaming answer: {str(e)}"
        )


@router.post("/chat/stream")
@limiter.limit(settings.rate_limit)
def chat_stream(request: Request, payload: ChatRequest):
    session_id, conversation = get_or_create_session(payload.session_id)

    def event_stream():
        # First event sends the session_id back to the client so it can reuse it
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"
        yield from stream_chat(conversation, payload.message, session_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
