from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from backend.app.schemas.query import ChatRequest
from backend.app.rag.orchestrator import stream_chat
from backend.app.core.session_store import get_or_create_session
from backend.app.core.rate_limit import limiter
from backend.app.core.config import settings
import json

router = APIRouter()


@router.post("/chat/stream")
@limiter.limit(settings.rate_limit)
def chat_stream(request: Request, payload: ChatRequest):
    session_id, conversation = get_or_create_session(payload.session_id)

    def event_stream():
        # First event sends the session_id back to the client so it can reuse it
        yield f"event: session\ndata: {json.dumps({'session_id': session_id})}\n\n"
        yield from stream_chat(conversation, payload.message, session_id)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
