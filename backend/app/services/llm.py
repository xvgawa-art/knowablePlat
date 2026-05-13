import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()

_client = AsyncAnthropic(api_key=settings.anthropic_auth_token, base_url=settings.anthropic_base_url)


class LLMResponse:
    """Response from LLM generate call with text and usage metadata."""

    __slots__ = ("text", "input_tokens", "output_tokens")

    def __init__(self, text: str, input_tokens: int = 0, output_tokens: int = 0):
        self.text = text
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


async def generate(prompt: str, system: str = "") -> str:
    """Generate text using the configured LLM.

    Returns just the text string for backward compatibility.
    Use generate_with_usage() when you need token counts.
    """
    result = await generate_with_usage(prompt, system)
    return result.text


async def generate_with_usage(prompt: str, system: str = "") -> LLMResponse:
    """Generate text using the configured LLM, returning usage metadata."""
    kwargs: dict = {
        "model": settings.anthropic_model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = await _client.messages.create(**kwargs)
    text = response.content[0].text
    input_tokens = getattr(response.usage, "input_tokens", 0)
    output_tokens = getattr(response.usage, "output_tokens", 0)
    logger.info("llm_generate", model=settings.anthropic_model, input_tokens=input_tokens, output_tokens=output_tokens)
    return LLMResponse(text, input_tokens, output_tokens)


async def generate_structured(prompt: str, schema: type[BaseModel], system: str = "") -> BaseModel:
    """Generate structured output using the configured LLM with tool use."""
    tool_name = schema.__name__
    tool_schema = schema.model_json_schema()

    kwargs: dict = {
        "model": settings.anthropic_model,
        "max_tokens": 4096,
        "tools": [
            {
                "name": tool_name,
                "description": f"Generate a {tool_name}",
                "input_schema": tool_schema,
            }
        ],
        "tool_choice": {"type": "tool", "name": tool_name},
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = await _client.messages.create(**kwargs)

    for block in response.content:
        if block.type == "tool_use":
            return schema.model_validate(block.input)

    raise ValueError("LLM did not return structured output")


async def embed(text: str) -> list[float]:
    """Generate embedding vector for text via the LLM provider's embedding endpoint."""
    import httpx

    base = settings.anthropic_base_url.rstrip("/")
    embed_url = base.replace("/api/anthropic", "/api/paas/v4/embeddings")
    async with httpx.AsyncClient() as http:
        resp = await http.post(
            embed_url,
            json={"model": "embedding-3", "input": text[:2000]},
            headers={"Authorization": f"Bearer {settings.anthropic_auth_token}", "Content-Type": "application/json"},
            timeout=30,
        )
    resp.raise_for_status()
    data = resp.json()
    return data["data"][0]["embedding"]
