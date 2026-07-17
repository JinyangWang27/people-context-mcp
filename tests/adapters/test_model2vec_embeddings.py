"""Pinned Model2Vec snapshot selection tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from people_context.adapters.model2vec_embeddings import (
    MODEL_REPOSITORY,
    MODEL_REVISION,
    download_embedding_provider,
)

pytest.importorskip("model2vec")


class _Model:
    dim = 256


class _StaticModel:
    loaded_path: str | None = None

    @classmethod
    def from_pretrained(cls, path: str, *, force_download: bool) -> _Model:
        assert force_download is False
        cls.loaded_path = path
        return _Model()


def test_download_fetches_only_files_required_by_model2vec(monkeypatch: Any, tmp_path: Path) -> None:
    calls: list[dict[str, object]] = []
    cache_dir = tmp_path / "hub-cache"

    def snapshot_download(**kwargs: object) -> str:
        calls.append(kwargs)
        return str(tmp_path)

    monkeypatch.setattr("huggingface_hub.snapshot_download", snapshot_download)
    monkeypatch.setattr("model2vec.StaticModel", _StaticModel)
    monkeypatch.setenv("HF_HUB_CACHE", str(cache_dir))

    provider = download_embedding_provider()

    assert provider.dimension == 256
    assert _StaticModel.loaded_path == str(tmp_path)
    assert calls == [
        {
            "repo_id": MODEL_REPOSITORY,
            "revision": MODEL_REVISION,
            "cache_dir": cache_dir,
            "allow_patterns": ["README.md", "config.json", "model.safetensors", "tokenizer.json"],
            "local_files_only": False,
        }
    ]
