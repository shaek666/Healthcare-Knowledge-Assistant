import json, threading
from dataclasses import asdict, dataclass
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
        self._load()

    def saveState(self) -> None:
        self.metadataPath.parent.mkdir(parents=True, exist_ok=True)
        self.metadataPath.write_text(json.dumps(self.dataState, ensure_ascii=False, indent=2), encoding="utf-8")

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

    def _load(self) -> None:
        if not self.metadataPath.exists():
            return
        textContent = self.metadataPath.read_text(encoding="utf-8").strip()
        if not textContent:
            return
        rawState = json.loads(textContent)
        if isinstance(rawState, dict):
            self.dataState.update(
                {
                    "nextId": int(rawState.get("nextId", self.dataState["nextId"])),
                    "documents": rawState.get("documents", []),
                }
            )
