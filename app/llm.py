import json
import litellm
from pydantic import BaseModel
from typing import Type, TypeVar
from app.config import settings

litellm.drop_params = True  # ignore unsupported params per provider

T = TypeVar("T", bound=BaseModel)


async def chat(messages: list[dict], temperature: float = 0.2) -> str:
    """Plain text completion."""
    resp = await litellm.acompletion(
        model=settings.llm_model,
        messages=messages,
        temperature=temperature,
        api_key=settings.gemini_api_key,
    )
    return resp.choices[0].message.content


async def structured(
    messages: list[dict],
    schema: Type[T],
    temperature: float = 0.2,
) -> T:
    """Completion forced to match a Pydantic schema."""
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
    )
    raw = resp.choices[0].message.content
    # Strip code fences if model added them anyway
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return schema.model_validate_json(raw)
