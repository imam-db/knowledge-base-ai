from __future__ import annotations

from app.prompts import build_prompt, get_guardrail_message, get_system_instructions


def test_system_prompt_is_english():
    text = get_system_instructions()
    assert "handbook" in text.lower()
    assert "premier league" in text.lower()
    assert "Context:" not in text


def test_guardrail_message_loaded_from_file():
    guardrail = get_guardrail_message()
    assert guardrail == "Sorry, that information was not found in the available documents."


def test_build_prompt_uses_system_file_content():
    from app.retrieve import SearchResult

    chunk = SearchResult(
        rank=1,
        document_name="doc.pdf",
        page=1,
        chunk_id=0,
        distance=1.0,
        text="Document content.",
    )
    prompt = build_prompt("What is this?", [chunk])
    assert get_system_instructions() in prompt
    assert "Document content." in prompt
    assert "What is this?" in prompt
    assert "Context:" in prompt
    assert "Question:" in prompt
