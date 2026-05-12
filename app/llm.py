import contextvars
import json
from typing import Type, TypeVar

import litellm
from pydantic import BaseModel

from app.config import settings

litellm.drop_params = True

# Auto-instrument all LiteLLM calls if Langfuse keys are set
if settings.langfuse_public_key and settings.langfuse_secret_key:
    import os

    os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
    os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
    os.environ["LANGFUSE_HOST"] = settings.langfuse_host
    litellm.success_callback = ["langfuse"]
    litellm.failure_callback = ["langfuse"]

# Context-local trace ID — set by trace_run, read by LLM calls
current_trace_id: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "current_trace_id", default=None
)

T = TypeVar("T", bound=BaseModel)


def _trace_metadata() -> dict:
    tid = current_trace_id.get()
    if tid:
        return {"metadata": {"existing_trace_id": tid}}
    return {}


async def chat(messages: list[dict], temperature: float = 0.2) -> str:
    resp = await litellm.acompletion(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        api_key=settings.gemini_api_key,
        **_trace_metadata(),
    )
    return resp.choices[0].message.content


async def structured(
    messages: list[dict],
    schema: Type[T],
    temperature: float = 0.2,
) -> T:
    schema_json = schema.model_json_schema()
    sys_prompt = (
        "Respond with ONLY valid JSON matching this schema. "
        "No markdown, no commentary, no code fences.\n"
        f"Schema: {json.dumps(schema_json)}"
    )
    msgs = [{"role": "system", "content": sys_prompt}] + messages
    resp = await litellm.acompletion(
        model=settings.llm_model,
        messages=msgs,
        temperature=temperature,
        api_key=settings.gemini_api_key,
        response_format={"type": "json_object"},
        **_trace_metadata(),
    )
    raw = resp.choices[0].message.content
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return schema.model_validate_json(raw)
