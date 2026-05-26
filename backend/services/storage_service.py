from __future__ import annotations

import os
import re
from pathlib import Path
from uuid import uuid4

from backend.models.schemas import DocumentItem
from backend.services.utils import utc_now


class LocalDocumentStorageService:
    def upload_root(self) -> Path:
        override = os.getenv("VISAFLOW_UPLOAD_DIR", "").strip()
        if override:
            return Path(override)
        return Path(__file__).resolve().parents[2] / "data" / "uploads"

    def public_uri(self, case_id: str, filename: str) -> str:
        return f"/uploads/{case_id}/{filename}"

    def save_case_document(
        self,
        case_id: str,
        document_type: str,
        *,
        original_filename: str,
        content: bytes,
    ) -> DocumentItem:
        normalized_type = str(document_type or "").strip().upper()
        safe_name = self._safe_filename(original_filename or f"{normalized_type.lower()}.bin")
        suffix = Path(safe_name).suffix or ".bin"
        target_dir = self.upload_root() / case_id
        target_dir.mkdir(parents=True, exist_ok=True)

        target_path = target_dir / f"{normalized_type.lower()}-{uuid4().hex[:10]}{suffix}"
        target_path.write_bytes(content)

        return DocumentItem(
            document_id=f"DOC-UPL-{uuid4().hex[:8].upper()}",
            document_type=normalized_type,
            file_uri=self.public_uri(case_id, target_path.name),
            uploaded_at=utc_now(),
            status="UPLOADED",
        )

    def _safe_filename(self, filename: str) -> str:
        return re.sub(r"[^A-Za-z0-9._-]", "_", filename)
