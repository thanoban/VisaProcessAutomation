from __future__ import annotations

import json
import os
from functools import lru_cache


@lru_cache(maxsize=1)
def load_policy_manifest() -> dict:
    base_dir = os.getenv(
        "VISAFLOW_POLICY_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "rag", "visa_policy_documents"),
    )
    manifest_path = os.path.join(base_dir, "tourist_policy_manifest.json")
    with open(manifest_path, "r", encoding="utf-8") as handle:
        return json.load(handle)
