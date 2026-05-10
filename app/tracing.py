from contextlib import asynccontextmanager, contextmanager

import structlog
from langfuse import Langfuse

from app.config import settings
from app.llm import current_trace_id

log = structlog.get_logger()

_client: Langfuse | None = None


def get_client() -> Langfuse | None:
    global _client
    if _client is not None:
        return _client
    if not (settings.langfuse_public_key and settings.langfuse_secret_key):
        return None
    _client = Langfuse(
        public_key=settings.langfuse_public_key,
        secret_key=settings.langfuse_secret_key,
        host=settings.langfuse_host,
    )
    return _client


@asynccontextmanager
async def trace_run(name: str, input_data: dict):
    client = get_client()
    if client is None:
        yield None
        return
    trace = client.trace(name=name, input=input_data)
    token = current_trace_id.set(trace.id)
    try:
        yield trace
    finally:
        current_trace_id.reset(token)
        try:
            client.flush()
        except Exception as e:
            log.warning("langfuse_flush_failed", error=str(e))


@contextmanager
def node_span(name: str, input_data: dict | None = None):
    """Create a child span on the current trace. No-op if Langfuse disabled."""
    client = get_client()
    tid = current_trace_id.get()
    if client is None or not tid:
        yield None
        return
    span = client.span(trace_id=tid, name=name, input=input_data or {})
    try:
        yield span
    finally:
        try:
            span.end()
        except Exception:
            pass
