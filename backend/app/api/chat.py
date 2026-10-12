"""POST /api/chat, backed by NVIDIA. Not streaming yet (streaming is the next stage)."""
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.providers.errors import ProviderError
from app.providers.nvidia import chat_completion

router = APIRouter(prefix="/api", tags=["chat"])

SYSTEM_PROMPT = "You are NEXUS, a helpful personal AI assistant."

STATUS_FOR_CODE = {
    "not_configured": 503,
    "auth": 502,
    "rate_limited": 429,
    "bad_request": 400,
    "timeout": 504,
    "unavailable": 503,
    "unknown": 502,
}


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=8000)
    model: str | None = Field(default=None, pattern=r"^[A-Za-z0-9._/-]{1,100}$")
    max_tokens: int = Field(default=1024, ge=16, le=4096)
    temperature: float = Field(default=0.3, ge=0, le=2)
    reasoning_effort: Literal["low", "high", "max"] | None = None
    include_reasoning: bool = False
    timeout_seconds: float | None = Field(default=None, ge=5, le=300)


class ChatResponse(BaseModel):
    model: str
    reply: str
    finish_reason: str | None = None
    warning: str | None = None
    usage: dict | None = None
    reasoning: str | None = None


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest) -> ChatResponse:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": req.message},
    ]
    try:
        result = await chat_completion(
            get_settings(),
            messages,
            model=req.model,
            max_tokens=req.max_tokens,
            temperature=req.temperature,
            reasoning_effort=req.reasoning_effort,
            timeout=req.timeout_seconds,
        )
    except ProviderError as exc:
        raise HTTPException(
            status_code=STATUS_FOR_CODE.get(exc.code, 502),
            detail={"code": exc.code, "message": exc.message, "retryable": exc.retryable},
        ) from None
    return ChatResponse(
        model=result["model"],
        reply=result["content"],
        finish_reason=result["finish_reason"],
        warning=result["warning"],
        usage=result["usage"],
        reasoning=result["reasoning"] if req.include_reasoning else None,
    )
