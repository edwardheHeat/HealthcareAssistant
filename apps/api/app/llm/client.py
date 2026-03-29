from openai import AsyncOpenAI

from app.config import settings

_client: AsyncOpenAI | None = None


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
