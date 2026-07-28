from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_HOME = Path.home() / ".spiral"
DEFAULT_CONFIG_PATH = DEFAULT_HOME / "session-manager.json"


@dataclass
class ManagerConfig:
    home: Path = field(default_factory=lambda: DEFAULT_HOME)
    coils_dir: Path | None = None
    index_path: Path | None = None
    require_approval: bool = True
    scan_paths: list[Path] = field(default_factory=list)
    recap_tool_root: Path | None = None

    def __post_init__(self) -> None:
        self.home = Path(self.home)
        if self.coils_dir is None:
            self.coils_dir = self.home / "coils"
        if self.index_path is None:
            self.index_path = self.home / "sessions" / "index.json"
        self.coils_dir = Path(self.coils_dir)
        self.index_path = Path(self.index_path)
        self.scan_paths = [Path(p) for p in self.scan_paths]
        if self.recap_tool_root is None:
            candidate = Path.home() / "Documents" / "GitHub" / "spiral-recap-tool"
            if candidate.exists():
                self.recap_tool_root = candidate

    @classmethod
    def load(cls, path: Path | None = None) -> ManagerConfig:
        config_path = path or DEFAULT_CONFIG_PATH
        if not config_path.exists():
            cfg = cls()
            if not cfg.scan_paths:
                cfg.scan_paths = cfg.default_scan_paths()
            cfg.ensure_dirs()
            cfg.save(config_path)
            return cfg

        data = json.loads(config_path.read_text(encoding="utf-8"))
        scan_paths = [Path(p) for p in data.get("scan_paths", [])]
        cfg = cls(
            home=Path(data.get("home", DEFAULT_HOME)),
            coils_dir=Path(data["coils_dir"]) if data.get("coils_dir") else None,
            index_path=Path(data["index_path"]) if data.get("index_path") else None,
            require_approval=data.get("require_approval", True),
            scan_paths=scan_paths,
            recap_tool_root=Path(data["recap_tool_root"])
            if data.get("recap_tool_root")
            else None,
        )
        if not cfg.scan_paths:
            cfg.scan_paths = cfg.default_scan_paths()
        cfg.ensure_dirs()
        return cfg

    def default_scan_paths(self) -> list[Path]:
        paths: list[Path] = []
        github = Path.home() / "Documents" / "GitHub"
        recap_examples = github / "spiral-recap-tool" / "examples"
        coil_grok = self.coils_dir / "grok" if self.coils_dir else DEFAULT_HOME / "coils" / "grok"
        if coil_grok.exists() or self.coils_dir:
            coil_grok.mkdir(parents=True, exist_ok=True)
            paths.append(coil_grok)
        if self.coils_dir:
            paths.append(self.coils_dir)
        if recap_examples.exists():
            paths.append(recap_examples)
        return paths

    def ensure_dirs(self) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        self.coils_dir.mkdir(parents=True, exist_ok=True)
        self.index_path.parent.mkdir(parents=True, exist_ok=True)

    def save(self, path: Path | None = None) -> None:
        config_path = path or DEFAULT_CONFIG_PATH
        config_path.parent.mkdir(parents=True, exist_ok=True)
        payload: dict[str, Any] = {
            "home": str(self.home),
            "coils_dir": str(self.coils_dir),
            "index_path": str(self.index_path),
            "require_approval": self.require_approval,
            "scan_paths": [str(p) for p in self.scan_paths],
            "recap_tool_root": str(self.recap_tool_root) if self.recap_tool_root else None,
        }
        config_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")