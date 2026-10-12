"""POST /api/chat/stream: server-sent events. Events: start, thinking, token, done, error."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.chat import SYSTEM_PROMPT, ChatRequest
from app.core.config import get_settings
from app.providers.nvidia_stream import stream_chat

router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]
    events = stream_chat(
        get_settings(),
        messages,
        model=req.model,
        max_tokens=req.max_tokens,
        temperature=req.temperature,
        reasoning_effort=req.reasoning_effort,
        timeout=req.timeout_seconds,
        include_reasoning=req.include_reasoning,
    )
    return StreamingResponse(
        events,
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
