import json
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

@dataclass
class DocumentRecord:
    id: int
    filename: str
    language: str
    content: str
    ingestedAt: str

class DocumentStore:
    def __init__(self, metadataPath: Path):
        self.metadataPath = metadataPath
        self.lockInstance = threading.RLock()
        self.dataState: Dict[str, object] = {"nextId": 1, "documents": []}
        self.loadState()

    def loadState(self) -> None:
        if self.metadataPath.exists():
            textContent = self.metadataPath.read_text(encoding="utf-8")
            if textContent.strip():
                self.dataState = json.loads(textContent)
        self.normalizeState()

    def saveState(self) -> None:
        self.metadataPath.parent.mkdir(parents=True, exist_ok=True)
        self.metadataPath.write_text(json.dumps(self.dataState, ensure_ascii=False, indent=2), encoding="utf-8")

    def normalizeState(self) -> None:
        if "next_id" in self.dataState:
            self.dataState["nextId"] = int(self.dataState.pop("next_id"))
        if "documents" not in self.dataState:
            self.dataState["documents"] = []
        normalizedDocuments: List[Dict[str, object]] = []
        for documentEntry in self.dataState["documents"]:
            normalizedEntry = dict(documentEntry)
            if "ingested_at" in normalizedEntry:
                normalizedEntry["ingestedAt"] = normalizedEntry.pop("ingested_at")
            normalizedDocuments.append(normalizedEntry)
        self.dataState["documents"] = normalizedDocuments
        if "nextId" not in self.dataState:
            self.dataState["nextId"] = 1

    def addDocument(self, filename: str, language: str, content: str) -> DocumentRecord:
        with self.lockInstance:
            documentId = int(self.dataState["nextId"])
            self.dataState["nextId"] = documentId + 1
            record = DocumentRecord(
                id=documentId,
                filename=filename,
                language=language,
                content=content,
                ingestedAt=datetime.now(timezone.utc).isoformat(),
            )
            documentsList: List[dict] = self.dataState.setdefault("documents", [])
            documentsList.append(asdict(record))
            self.saveState()
            return record

    def getDocument(self, documentId: int) -> Optional[DocumentRecord]:
        with self.lockInstance:
            for rawRecord in self.dataState.get("documents", []):
                if rawRecord["id"] == documentId:
                    return DocumentRecord(**rawRecord)
        return None

    def allDocuments(self) -> List[DocumentRecord]:
        with self.lockInstance:
            return [DocumentRecord(**rawRecord) for rawRecord in self.dataState.get("documents", [])]