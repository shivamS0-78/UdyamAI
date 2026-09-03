from unittest.mock import patch

from app.ai.llm import LLMError


def test_chat_endpoint_returns_llm_reply(client):
    with patch(
        "app.api.routes.chat.generate_chat_reply", return_value=("Hello from UdyamAI.", True)
    ):
        response = client.post("/api/v1/chat", json={"message": "What is PMEGP?"})
    assert response.status_code == 200
    data = response.json()
    assert data["reply"] == "Hello from UdyamAI."
    assert data["provider_available"] is True


def test_chat_falls_back_when_llm_unavailable():
    from app.ai import chat

    with patch("app.ai.chat.llm.generate", side_effect=LLMError("down")):
        reply, available = chat.generate_chat_reply("Hello")
    assert available is False
    assert "UdyamAI" in reply


def test_chat_fallback_hindi():
    from app.ai import chat
    from app.ai.llm import LLMError

    with patch("app.ai.chat.llm.generate", side_effect=LLMError("down")):
        reply, available = chat.generate_chat_reply("नमस्ते", language="hi")
    assert available is False
    assert "उद्यमएआई" in reply
