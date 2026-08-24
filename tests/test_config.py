from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app.config import load_settings


def _write_config(tmp_path: Path, yaml_body: str) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "config.yaml"
    path.write_text(textwrap.dedent(yaml_body), encoding="utf-8")
    return path


def test_load_settings_reads_app_name_and_chunk_size_from_yaml(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    config_path = _write_config(
        tmp_path,
        """
        app:
          name: Clinic Assistant
        chunking:
          size: 512
          overlap: 50
        retrieval:
          distance_threshold: 18.5
        """,
    )

    settings = load_settings(config_path)

    assert settings.app_name == "Clinic Assistant"
    assert settings.chunk_size == 512
    assert settings.chunk_overlap == 50
    assert settings.retrieval_distance_threshold == 18.5


def test_load_settings_reads_secrets_from_env_only(tmp_path, monkeypatch):
    monkeypatch.setenv("GROQ_API_KEY", "test-groq-key")
    monkeypatch.setenv("ADMIN_API_KEY", "test-admin-key")

    config_path = _write_config(
        tmp_path,
        """
        app:
          name: Knowledge Application
        """,
    )

    settings = load_settings(config_path)

    assert settings.groq_api_key == "test-groq-key"
    assert settings.admin_api_key == "test-admin-key"


def test_load_settings_reads_ui_mode_and_show_documents(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    config_path = _write_config(
        tmp_path,
        """
        app:
          name: PL Demo
        ui:
          mode: portfolio
          show_documents: false
          subtitle: Tanya handbook PL
          example_questions:
            - Pertanyaan satu
            - Pertanyaan dua
        """,
    )

    settings = load_settings(config_path)

    assert settings.ui.mode == "portfolio"
    assert settings.ui.show_documents is False
    assert settings.ui.subtitle == "Tanya handbook PL"
    assert settings.ui.example_questions == ["Pertanyaan satu", "Pertanyaan dua"]


def test_load_settings_playground_defaults_show_documents_true(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    config_path = _write_config(
        tmp_path,
        """
        app:
          name: Playground
        ui:
          mode: playground
        """,
    )

    settings = load_settings(config_path)

    assert settings.ui.mode == "playground"
    assert settings.ui.show_documents is True


def test_load_settings_reads_about_block(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    config_path = _write_config(
        tmp_path,
        """
        app:
          name: PL Demo
        ui:
          show_about: true
        about:
          title: Case study
          tagline: A RAG demo
          problem: Long PDF
          approach: Chunk and retrieve
          pipeline:
            - label: Ingest
              detail: PDF to chunks
          guardrails:
            - Grounded only
          tradeoffs:
            - English corpus
          eval:
            dataset: evals/test.jsonl
            questions: 10
            hit_at_5: 0.8
            mrr: 0.65
            note: Test run
        """,
    )

    settings = load_settings(config_path)

    assert settings.ui.show_about is True
    assert settings.about is not None
    assert settings.about.title == "Case study"
    assert len(settings.about.pipeline) == 1
    assert settings.about.pipeline[0].label == "Ingest"
    assert settings.about.eval is not None
    assert settings.about.eval.hit_at_5 == 0.8


def test_load_settings_show_about_defaults_by_mode(tmp_path, monkeypatch):
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ADMIN_API_KEY", raising=False)

    portfolio_path = _write_config(
        tmp_path / "portfolio",
        """
        app:
          name: Portfolio
        ui:
          mode: portfolio
        """,
    )
    playground_path = _write_config(
        tmp_path / "playground",
        """
        app:
          name: Playground
        ui:
          mode: playground
        """,
    )

    assert load_settings(portfolio_path).ui.show_about is True
    assert load_settings(playground_path).ui.show_about is False


def test_load_settings_missing_config_raises(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_settings(missing)
