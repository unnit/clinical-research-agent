import asyncio
import json
from typing import AsyncIterator
from pydantic import BaseModel
from time import time


class ProgressEvent(BaseModel):
    """One SSE event emitted by the graph."""
    type: str  # "node_start" | "node_end" | "complete" | "error"
    node: str = ""
    elapsed_ms: int = 0
    detail: dict = {}


class ProgressQueue:
    """Async pipe that nodes push to and the SSE endpoint reads from."""

    SENTINEL = object()  # marks "no more events"

    def __init__(self):
        self._q: asyncio.Queue = asyncio.Queue()
        self._start = time()

    def _elapsed(self) -> int:
        return int((time() - self._start) * 1000)

    async def emit(self, type_: str, node: str = "", **detail):
        await self._q.put(ProgressEvent(
            type=type_,
            node=node,
            elapsed_ms=self._elapsed(),
            detail=detail,
        ))

    async def close(self):
        await self._q.put(self.SENTINEL)

    async def events(self) -> AsyncIterator[str]:
        """SSE-formatted event stream."""
        while True:
            item = await self._q.get()
            if item is self.SENTINEL:
                return
            yield f"data: {json.dumps(item.model_dump())}\n\n"
