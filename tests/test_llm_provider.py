from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.core.llm import GroqProvider, get_llm_provider


def test_groq_provider_generate_returns_content():
    mock_response = MagicMock()
    mock_response.choices = [MagicMock(message=MagicMock(content="  jawaban  "))]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = mock_response

    with (
        patch("app.core.llm.Groq", return_value=mock_client),
        patch("app.core.llm.settings") as settings_mock,
    ):
        settings_mock.groq_api_key = "key"
        settings_mock.groq_model = "test-model"
        provider = GroqProvider()
        assert provider.generate("prompt") == "jawaban"

    mock_client.chat.completions.create.assert_called_once()


def test_call_groq_uses_llm_provider():
    from app.llm import call_groq

    with patch("app.llm.get_llm_provider") as get_provider:
        provider = MagicMock()
        provider.generate.return_value = "ok"
        get_provider.return_value = provider
        assert call_groq("hi") == "ok"
        provider.generate.assert_called_once_with("hi")


def test_get_llm_provider_is_singleton():
    # Reset module singleton for isolation
    import app.core.llm as llm_mod

    llm_mod._default_provider = None
    a = get_llm_provider()
    b = get_llm_provider()
    assert a is b
