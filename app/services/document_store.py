"""Persistent JSON backing store for ingested documents."""

from __future__ import annotations

import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class DocumentRecord:
    """Metadata for an ingested document."""

    id: int
    filename: str
    language: str
    content: str
    ingested_at: str


class DocumentStore:
    """Thread-safe storage for document metadata and content."""

    def __init__(self, metadata_path: Path):
        self.metadata_path = metadata_path
        self._lock = threading.RLock()
        self._data: Dict[str, object] = {"next_id": 1, "documents": []}
        self._load()

    def _load(self) -> None:
        if self.metadata_path.exists():
            text = self.metadata_path.read_text(encoding="utf-8")
            if text.strip():
                self._data = json.loads(text)

    def _save(self) -> None:
        self.metadata_path.parent.mkdir(parents=True, exist_ok=True)
        self.metadata_path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add_document(self, filename: str, language: str, content: str) -> DocumentRecord:
        """Persist the document and return its record."""

        with self._lock:
            document_id = int(self._data["next_id"])
            self._data["next_id"] = document_id + 1

            record = DocumentRecord(
                id=document_id,
                filename=filename,
                language=language,
                content=content,
                ingested_at=datetime.now(timezone.utc).isoformat(),
            )
            documents: List[dict] = self._data.setdefault("documents", [])
            documents.append(asdict(record))
            self._save()
            return record

    def get_document(self, document_id: int) -> Optional[DocumentRecord]:
        """Return a document record by id."""

        with self._lock:
            for raw in self._data.get("documents", []):
                if raw["id"] == document_id:
                    return DocumentRecord(**raw)
        return None

    def all_documents(self) -> List[DocumentRecord]:
        """Return all stored records."""

        with self._lock:
            return [DocumentRecord(**raw) for raw in self._data.get("documents", [])]

