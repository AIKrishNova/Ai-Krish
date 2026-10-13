"""POST /api/chat/stream: server-sent events. Events: start, thinking, token, done, error."""
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.api.chat import SYSTEM_PROMPT, ChatRequest
from app.core.config import get_settings
from app.providers.nvidia_stream import stream_chat

GROUNDING = (
    "\n\nYou have no internet access and cannot browse or search the web. "
    "If asked to search or for current events, say so plainly, then answer "
    "from general knowledge and mention it may be out of date. "
    "Do not invent sources, links, or live data."
)


router = APIRouter(prefix="/api", tags=["chat"])


@router.post("/chat/stream")
async def chat_stream(req: ChatRequest) -> StreamingResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + GROUNDING},
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
