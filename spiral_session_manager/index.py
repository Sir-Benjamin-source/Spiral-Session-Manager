from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass
class CoilRecord:
    path: str
    title: str
    date: str = ""
    convergence: str = ""
    key_motifs: list[str] = field(default_factory=list)
    poetic_seal: str = ""
    companion_path: str | None = None
    project_slug: str = ""
    indexed_at: str = ""
    mtime: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CoilRecord:
        return cls(
            path=data["path"],
            title=data.get("title", ""),
            date=data.get("date", ""),
            convergence=data.get("convergence", ""),
            key_motifs=list(data.get("key_motifs", [])),
            poetic_seal=data.get("poetic_seal", ""),
            companion_path=data.get("companion_path"),
            project_slug=data.get("project_slug", ""),
            indexed_at=data.get("indexed_at", ""),
            mtime=float(data.get("mtime", 0.0)),
        )


class CoilIndex:
    def __init__(self, path: Path) -> None:
        self.path = path
        self.coils: dict[str, CoilRecord] = {}
        self.companions: dict[str, str] = {}
        self.sessions: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        self.coils = {
            k: CoilRecord.from_dict(v) for k, v in data.get("coils", {}).items()
        }
        self.companions = dict(data.get("companions", {}))
        self.sessions = list(data.get("sessions", []))

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "version": 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "coils": {k: v.to_dict() for k, v in self.coils.items()},
            "companions": self.companions,
            "sessions": self.sessions,
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def upsert_coil(self, record: CoilRecord) -> None:
        key = str(Path(record.path).resolve())
        record.indexed_at = datetime.now(timezone.utc).isoformat()
        self.coils[key] = record
        if record.companion_path:
            self.companions[key] = record.companion_path

    def remove_missing(self, existing_paths: set[str]) -> int:
        removed = 0
        for key in list(self.coils.keys()):
            if key not in existing_paths:
                del self.coils[key]
                self.companions.pop(key, None)
                removed += 1
        return removed

    def list_coils(self, project_slug: str | None = None) -> list[CoilRecord]:
        records = list(self.coils.values())
        if project_slug:
            records = [r for r in records if r.project_slug == project_slug]
        return sorted(records, key=lambda r: r.mtime, reverse=True)

    def search(self, query: str, limit: int = 5) -> list[tuple[CoilRecord, float]]:
        if not query.strip():
            return []

        terms = [t.lower() for t in query.split() if t.strip()]
        scored: list[tuple[CoilRecord, float]] = []

        for record in self.coils.values():
            haystack = " ".join(
                [
                    record.title,
                    record.date,
                    record.convergence,
                    record.poetic_seal,
                    " ".join(record.key_motifs),
                    record.project_slug,
                ]
            ).lower()
            score = 0.0
            for term in terms:
                if term in haystack:
                    score += 1.0
                for motif in record.key_motifs:
                    if term in motif.lower():
                        score += 1.5
            if score > 0:
                scored.append((record, score))

        scored.sort(key=lambda item: (item[1], item[0].mtime), reverse=True)
        return scored[:limit]

    def log_session_close(
        self,
        cwd: str,
        title: str,
        coil_path: str | None = None,
        notes: str = "",
    ) -> None:
        self.sessions.append(
            {
                "closed_at": datetime.now(timezone.utc).isoformat(),
                "cwd": cwd,
                "title": title,
                "coil_path": coil_path,
                "notes": notes,
            }
        )
        self.sessions = self.sessions[-200:]