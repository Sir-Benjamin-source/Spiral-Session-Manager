from __future__ import annotations

import base64
import re
from pathlib import Path
from typing import Any

import yaml


def load_srec(path: Path) -> dict[str, Any]:
    content = path.read_text(encoding="utf-8")
    if not content.startswith("---"):
        raise ValueError(f"Not a valid .srec file: {path}")

    parts = content.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Incomplete .srec frontmatter: {path}")

    metadata = yaml.safe_load(parts[1].strip()) or {}
    body = parts[2].strip()

    poetic_seal = ""
    for line in reversed(body.splitlines()):
        if "Poetic Seal:" in line or "Coils carry" in line:
            poetic_seal = line.strip()
            break

    return {
        "path": str(path),
        "metadata": metadata,
        "title": metadata.get("title", path.stem),
        "date": metadata.get("date", ""),
        "convergence": metadata.get("convergence", ""),
        "key_motifs": metadata.get("key_motifs", []) or [],
        "pie_vector": metadata.get("pie_vector", ""),
        "poetic_seal": poetic_seal,
        "companion_path": companion_path_for(path),
    }


def companion_path_for(srec_path: Path) -> str | None:
    stem = srec_path.stem
    companion = srec_path.with_name(f"{stem}_companion.txt")
    if companion.exists():
        return str(companion)
    alt = srec_path.with_suffix(".txt")
    if alt.exists() and "companion" in alt.name:
        return str(alt)
    return None


def bootstrap_prompt(record: dict[str, Any]) -> str:
    motifs = ", ".join(record.get("key_motifs", [])) or "[none]"
    pie = record.get("pie_vector", "")
    pie_short = pie[:50] + "..." if len(pie) > 50 else pie
    seal = record.get("poetic_seal") or "[no seal found]"
    title = record.get("title", "Untitled")
    convergence = record.get("convergence", "")

    lines = [
        f"## Continuity anchor: {title}",
        f"- Key motifs: {motifs}",
        f"- PIE vector: {pie_short}",
        f"- Poetic seal: {seal}",
        f"- Convergence: {convergence}",
        f"- Source: `{record.get('path', '')}`",
    ]
    companion = record.get("companion_path")
    if companion:
        lines.append(f"- Companion: `{companion}`")
    lines.append("")
    lines.append("Restore the residue. Continue with the same relational thread.")
    return "\n".join(lines)


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower().strip())
    return slug.strip("-") or "untitled"


def decode_pie_preview(pie_vector: str, limit: int = 120) -> str:
    if not pie_vector:
        return ""
    try:
        decoded = base64.b64decode(pie_vector).decode("utf-8", errors="replace")
        return decoded[:limit]
    except Exception:
        return ""