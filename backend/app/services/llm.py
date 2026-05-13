import structlog
from anthropic import AsyncAnthropic
from pydantic import BaseModel

from app.config import settings

logger = structlog.get_logger()

_client = AsyncAnthropic(api_key=settings.anthropic_auth_token, base_url=settings.anthropic_base_url)


async def generate(prompt: str, system: str = "") -> str:
    """Generate text using the configured LLM."""
    kwargs: dict = {
        "model": settings.anthropic_model,
        "max_tokens": 4096,
        "messages": [{"role": "user", "content": prompt}],
    }
    if system:
        kwargs["system"] = system

    response = await _client.messages.create(**kwargs)
    text = response.content[0].text
    logger.info("llm_generate", model=settings.anthropic_model, input_tokens=getattr(response.usage, "input_tokens", 0))
    return text


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
