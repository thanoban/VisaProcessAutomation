from __future__ import annotations

import json
import os
from functools import lru_cache


def _repo_rag_dir(*parts: str) -> str:
    return os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "rag", *parts)


def _policy_dir() -> str:
    return os.getenv(
        "VISAFLOW_POLICY_DIR",
        _repo_rag_dir("visa_policy_documents"),
    )


def _reference_dir() -> str:
    return os.getenv(
        "VISAFLOW_REFERENCE_DATA_DIR",
        _repo_rag_dir("reference_data"),
    )


@lru_cache(maxsize=32)
def _load_json_file(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def load_policy_manifest() -> dict:
    manifest_path = os.path.join(_policy_dir(), "tourist_policy_manifest.json")
    return _load_json_file(manifest_path)


def load_reference_json(filename: str) -> dict:
    reference_path = os.path.join(_reference_dir(), filename)
    return _load_json_file(reference_path)


def clear_policy_caches() -> None:
    _load_json_file.cache_clear()
