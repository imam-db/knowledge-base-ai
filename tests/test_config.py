from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from app.config import load_settings


def _write_config(tmp_path: Path, yaml_body: str) -> Path:
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


def test_load_settings_missing_config_raises(tmp_path):
    missing = tmp_path / "missing.yaml"
    with pytest.raises(FileNotFoundError, match="Config file not found"):
        load_settings(missing)
