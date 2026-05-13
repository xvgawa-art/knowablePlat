import json
import uuid
from unittest.mock import patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.llm import LLMResponse


@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c


class TestGenerateService:
    async def test_generate_document_full_pipeline(self):
        from app.services.generate import generate_document

        sample_knowledge = (
            "## 知识库：Web 安全\n\n"
            "# Web 安全索引\n\n- [[xss]] XSS 攻击\n\n"
            "---\n\n"
            "## 知识库：AI 安全\n\n"
            "# AI 安全索引\n\n- [[prompt-injection]] 提示注入攻击"
        )

        outline_json = json.dumps(
            {"title": "XSS 攻击全解析", "sections": [{"heading": "XSS 类型", "key_points": ["反射型", "存储型"]}]},
            ensure_ascii=False,
        )

        call_count = 0

        async def mock_generate_with_usage(prompt, system=""):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                text = f"```json\n{outline_json}\n```"
            elif call_count == 2:
                text = "XSS 攻击分为反射型和存储型两种主要类型..."
            else:
                text = "# XSS 攻击全解析\n\n## XSS 类型\n\nXSS 攻击分为反射型和存储型..."
            return LLMResponse(text, input_tokens=50, output_tokens=100)

        with (
            patch("app.services.generate.retrieve_knowledge", return_value=sample_knowledge),
            patch("app.services.generate.generate_with_usage", side_effect=mock_generate_with_usage),
        ):
            result = await generate_document([str(uuid.uuid4())], "XSS 攻击")
            assert result["title"] == "XSS 攻击全解析"
            assert result["content"] is not None
            assert result["word_count"] > 0
            assert result["token_usage"] > 0
            assert call_count == 3  # outline + section + integrate

    async def test_generate_document_outline_parse_fallback(self):
        from app.services.generate import generate_document

        sample_knowledge = "## 知识库：测试\n\n一些内容"
        call_count = 0

        async def mock_generate_with_usage(prompt, system=""):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                text = "This is not valid JSON at all"
            elif call_count == 2:
                text = "Section content here"
            else:
                text = "# Fallback Document\n\n## Test Topic\n\nSection content here"
            return LLMResponse(text, input_tokens=10, output_tokens=20)

        with (
            patch("app.services.generate.retrieve_knowledge", return_value=sample_knowledge),
            patch("app.services.generate.generate_with_usage", side_effect=mock_generate_with_usage),
        ):
            result = await generate_document([str(uuid.uuid4())], "Test Topic")
            assert result["title"] == "Test Topic"
            assert result["content"] is not None


class TestGenerateAPI:
    async def test_create_and_list_generation(self, client: AsyncClient):
        kb_resp = await client.post(
            "/api/knowledge-bases",
            json={"name": f"生成测试-{uuid.uuid4().hex[:6]}", "slug": f"gen-{uuid.uuid4().hex[:6]}"},
        )
        assert kb_resp.status_code == 201
        kb_id = kb_resp.json()["id"]

        with (
            patch("app.services.generate.retrieve_knowledge", return_value="知识内容"),
            patch("app.services.generate.generate_with_usage", return_value=LLMResponse("生成结果", 10, 20)),
        ):
            resp = await client.post(
                "/api/generate",
                json={"kb_ids": [kb_id], "topic": "测试主题"},
            )
            assert resp.status_code == 201
            data = resp.json()
            assert data["status"] == "generating"
            doc_id = data["id"]

        list_resp = await client.get("/api/generate")
        assert list_resp.status_code == 200
        titles = [item["title"] for item in list_resp.json()]
        assert "测试主题" in titles

        get_resp = await client.get(f"/api/generate/{doc_id}")
        assert get_resp.status_code == 200
        assert get_resp.json()["topic"] == "测试主题"

    async def test_create_generation_empty_kb_ids(self, client: AsyncClient):
        resp = await client.post("/api/generate", json={"kb_ids": [], "topic": "Test"})
        assert resp.status_code in (400, 422)

    async def test_create_generation_empty_topic(self, client: AsyncClient):
        resp = await client.post("/api/generate", json={"kb_ids": ["id"], "topic": "  "})
        assert resp.status_code == 400

    async def test_get_generation_not_found(self, client: AsyncClient):
        resp = await client.get(f"/api/generate/{uuid.uuid4()}")
        assert resp.status_code == 404

    async def test_delete_generation(self, client: AsyncClient):
        kb_resp = await client.post(
            "/api/knowledge-bases",
            json={"name": f"删除测试-{uuid.uuid4().hex[:6]}", "slug": f"del-{uuid.uuid4().hex[:6]}"},
        )
        kb_id = kb_resp.json()["id"]

        with (
            patch("app.services.generate.retrieve_knowledge", return_value="知识"),
            patch("app.services.generate.generate_with_usage", return_value=LLMResponse("结果", 10, 20)),
        ):
            resp = await client.post(
                "/api/generate",
                json={"kb_ids": [kb_id], "topic": "待删除"},
            )
            doc_id = resp.json()["id"]

        del_resp = await client.delete(f"/api/generate/{doc_id}")
        assert del_resp.status_code == 204

        get_resp = await client.get(f"/api/generate/{doc_id}")
        assert get_resp.status_code == 404
