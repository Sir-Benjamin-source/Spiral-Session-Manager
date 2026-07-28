from __future__ import annotations

import shutil
from datetime import datetime, timezone
from pathlib import Path

from .config import ManagerConfig
from .index import CoilIndex, CoilRecord
from .srec_io import bootstrap_prompt, load_srec, slugify


class SessionManager:
    def __init__(self, config: ManagerConfig | None = None) -> None:
        self.config = config or ManagerConfig.load()
        self.index = CoilIndex(self.config.index_path)

    def project_slug(self, cwd: Path | None = None) -> str:
        cwd = (cwd or Path.cwd()).resolve()
        if (cwd / ".git").exists():
            try:
                import subprocess

                result = subprocess.run(
                    ["git", "remote", "get-url", "origin"],
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0 and result.stdout.strip():
                    remote = result.stdout.strip()
                    if "/" in remote:
                        repo = remote.rstrip("/").split("/")[-1]
                        if repo.endswith(".git"):
                            repo = repo[:-4]
                        return slugify(repo)
            except Exception:
                pass
        return slugify(cwd.name)

    def discover_srec_files(self) -> list[Path]:
        found: dict[str, Path] = {}
        for root in self.config.scan_paths:
            if not root.exists():
                continue
            for path in root.rglob("*.srec"):
                found[str(path.resolve())] = path.resolve()
        return list(found.values())

    def index_all(self, cwd: Path | None = None) -> dict[str, int]:
        cwd = cwd or Path.cwd()
        slug = self.project_slug(cwd)
        discovered = self.discover_srec_files()
        indexed = 0
        existing: set[str] = set()

        for path in discovered:
            try:
                parsed = load_srec(path)
            except Exception:
                continue

            key = str(path.resolve())
            existing.add(key)
            stat = path.stat()
            record = CoilRecord(
                path=key,
                title=parsed.get("title", path.stem),
                date=parsed.get("date", ""),
                convergence=parsed.get("convergence", ""),
                key_motifs=list(parsed.get("key_motifs", [])),
                poetic_seal=parsed.get("poetic_seal", ""),
                companion_path=parsed.get("companion_path"),
                project_slug=slug if str(path).startswith(str(cwd.resolve())) else slugify(path.parent.name),
                mtime=stat.st_mtime,
            )
            self.index.upsert_coil(record)
            indexed += 1

        removed = self.index.remove_missing(existing)
        self.index.save()
        return {"indexed": indexed, "removed": removed, "total": len(self.index.coils)}

    def organize_inbox(self, source_dir: Path, category: str = "Grok") -> list[str]:
        source_dir = source_dir.resolve()
        if not source_dir.exists():
            raise FileNotFoundError(source_dir)

        target_root = self.config.coils_dir / category.lower()
        target_root.mkdir(parents=True, exist_ok=True)
        moved: list[str] = []

        for srec_path in source_dir.glob("*.srec"):
            target = target_root / srec_path.name
            if not target.exists():
                shutil.copy2(srec_path, target)
            companion = srec_path.with_name(f"{srec_path.stem}_companion.txt")
            if companion.exists():
                comp_target = target_root / companion.name
                if not comp_target.exists():
                    shutil.copy2(companion, comp_target)
            moved.append(str(target))

        if moved and target_root not in self.config.scan_paths:
            self.config.scan_paths.append(target_root)
            self.config.save()

        self.index_all()
        return moved

    def bootstrap(self, cwd: Path | None = None, query: str | None = None) -> str:
        cwd = cwd or Path.cwd()
        self.index_all(cwd=cwd)
        slug = self.project_slug(cwd)
        coils = self.index.list_coils(project_slug=slug)
        if not coils:
            coils = self.index.list_coils()

        if query:
            matches = self.index.search(query, limit=3)
            if matches:
                blocks = [bootstrap_prompt(match[0].to_dict()) for match in matches]
                return "\n\n".join(blocks)

        if not coils:
            return (
                "No indexed .srec coils found. Run `spiral-session index` after creating recaps, "
                "or say `spiral recap` to archive this session."
            )

        latest = coils[0]
        return bootstrap_prompt(latest.to_dict())

    def pull_context(
        self,
        query: str,
        *,
        approve: bool = False,
        limit: int = 3,
    ) -> str:
        matches = self.index.search(query, limit=limit)
        if not matches:
            return f"No coils matched '{query}'. Try `spiral-session list` or `spiral-session index`."

        if self.config.require_approval and not approve:
            titles = [f"- {rec.title} (score {score:.1f})" for rec, score in matches]
            return (
                "Context pull requires approval. Re-run with `--approve` after reviewing:\n"
                + "\n".join(titles)
            )

        blocks = []
        for record, score in matches:
            data = record.to_dict()
            data["match_score"] = score
            blocks.append(bootstrap_prompt(data))
            if record.companion_path and Path(record.companion_path).exists():
                companion_preview = Path(record.companion_path).read_text(encoding="utf-8")
                preview_lines = companion_preview.splitlines()[:20]
                blocks.append("### Companion preview\n" + "\n".join(preview_lines))
        return "\n\n---\n\n".join(blocks)

    def list_coils(self, project_slug: str | None = None) -> str:
        coils = self.index.list_coils(project_slug=project_slug)
        if not coils:
            return "No coils indexed."
        lines = ["| Title | Date | Motifs | Path |", "|---|---|---|---|"]
        for coil in coils[:30]:
            motifs = ", ".join(coil.key_motifs[:3]) or "—"
            lines.append(
                f"| {coil.title} | {coil.date or '—'} | {motifs} | `{coil.path}` |"
            )
        if len(coils) > 30:
            lines.append(f"\n… and {len(coils) - 30} more.")
        return "\n".join(lines)

    def close_session(
        self,
        title: str,
        cwd: Path | None = None,
        coil_path: str | None = None,
        notes: str = "",
    ) -> str:
        cwd = cwd or Path.cwd()
        self.index.log_session_close(str(cwd.resolve()), title, coil_path, notes)
        self.index.save()
        return f"Session logged: {title} @ {datetime.now(timezone.utc).isoformat()}"