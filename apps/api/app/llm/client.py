from openai import AsyncOpenAI, OpenAI

from app.config import settings

_client: AsyncOpenAI | None = None
_sync_client: OpenAI | None = None


def get_llm_client() -> AsyncOpenAI:
    """Return a shared AsyncOpenAI client configured from environment settings.

    Uses the OpenAI-compatible protocol, so any provider (Gemini, DeepSeek,
    OpenAI, etc.) can be used by pointing LLM_BASE_URL at the right endpoint.
    """
    global _client
    if _client is None:
        _client = AsyncOpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    return _client



async def call_llm(system: str, user: str) -> str:
    """Single-turn LLM call shared across chat_service, alert_writer, etc.

    Returns the assistant reply as a plain string.
    """
    client = get_llm_client()
    resp = await client.chat.completions.create(
        model=settings.llm_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return resp.choices[0].message.content or ""

def get_sync_llm_client() -> OpenAI:
    """Return a shared sync OpenAI client for background-style service work."""
    global _sync_client
    if _sync_client is None:
        _sync_client = OpenAI(
            base_url=settings.llm_base_url,
            api_key=settings.llm_api_key,
        )
    return _sync_client

