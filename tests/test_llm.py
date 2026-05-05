import pytest
from pydantic import BaseModel
from app.llm import chat, structured


class Greeting(BaseModel):
    greeting: str
    language: str


@pytest.mark.asyncio
async def test_chat_basic():
    out = await chat([{"role": "user", "content": "Say hi in one word."}])
    assert out
    print(f"\nResponse: {out}")


@pytest.mark.asyncio
async def test_structured_output():
    out = await structured(
        [{"role": "user", "content": "Greet me in French."}],
        schema=Greeting,
    )
    assert out.greeting
    assert out.language
    print(f"\nGreeting: {out.greeting} ({out.language})")
