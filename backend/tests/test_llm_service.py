from unittest.mock import AsyncMock, MagicMock, patch

import pytest


async def test_generate_with_usage_returns_llm_response() -> None:
    from app.services.llm import generate_with_usage

    mock_usage = MagicMock(input_tokens=10, output_tokens=20)
    mock_block = MagicMock(text="Hello world")
    mock_response = MagicMock(content=[mock_block], usage=mock_usage)

    with patch("app.services.llm._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await generate_with_usage("Say hello")
        assert result.text == "Hello world"
        assert result.input_tokens == 10
        assert result.output_tokens == 20
        assert result.total_tokens == 30


async def test_generate_returns_text_only() -> None:
    from app.services.llm import generate

    mock_usage = MagicMock(input_tokens=5, output_tokens=10)
    mock_block = MagicMock(text="Response text")
    mock_response = MagicMock(content=[mock_block], usage=mock_usage)

    with patch("app.services.llm._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await generate("test prompt")
        assert result == "Response text"


async def test_generate_with_system_prompt() -> None:
    from app.services.llm import generate_with_usage

    mock_usage = MagicMock(input_tokens=10, output_tokens=5)
    mock_block = MagicMock(text="Structured answer")
    mock_response = MagicMock(content=[mock_block], usage=mock_usage)

    with patch("app.services.llm._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await generate_with_usage("question", system="You are a helper")
        assert result.text == "Structured answer"

        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "You are a helper"


async def test_generate_structured_returns_model() -> None:
    from pydantic import BaseModel

    from app.services.llm import generate_structured

    class TestSchema(BaseModel):
        name: str
        value: int

    mock_block = MagicMock()
    mock_block.type = "tool_use"
    mock_block.input = {"name": "test", "value": 42}
    mock_response = MagicMock(content=[mock_block])

    with patch("app.services.llm._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        result = await generate_structured("extract data", TestSchema)
        assert isinstance(result, TestSchema)
        assert result.name == "test"
        assert result.value == 42


async def test_generate_structured_raises_when_no_tool_use() -> None:
    from pydantic import BaseModel

    from app.services.llm import generate_structured

    class DummySchema(BaseModel):
        x: int

    mock_block = MagicMock()
    mock_block.type = "text"
    mock_response = MagicMock(content=[mock_block])

    with patch("app.services.llm._client") as mock_client:
        mock_client.messages.create = AsyncMock(return_value=mock_response)

        with pytest.raises(ValueError, match="structured output"):
            await generate_structured("test", DummySchema)


async def test_embed_returns_vector() -> None:
    import httpx

    from app.services.llm import embed

    mock_resp = MagicMock()
    mock_resp.json = lambda: {"data": [{"embedding": [0.1, 0.2, 0.3]}]}
    mock_resp.raise_for_status = lambda: None

    with patch.object(httpx, "AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.post.return_value = mock_resp
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_client

        result = await embed("test text")
        assert result == [0.1, 0.2, 0.3]


def test_llm_response_total_tokens() -> None:
    from app.services.llm import LLMResponse

    resp = LLMResponse("text", input_tokens=100, output_tokens=50)
    assert resp.total_tokens == 150

    resp_zero = LLMResponse("text")
    assert resp_zero.total_tokens == 0
