from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import ManagerConfig
from .manager import SessionManager


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="spiral-session",
        description="Spiral Session Manager — index .srec coils and pull cross-session context.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    index_p = sub.add_parser("index", help="Scan configured paths and rebuild the coil index")
    index_p.add_argument("--cwd", type=Path, default=Path.cwd())

    sub.add_parser("list", help="List indexed coils")

    bootstrap_p = sub.add_parser("bootstrap", help="Print continuity anchors for session start")
    bootstrap_p.add_argument("--cwd", type=Path, default=Path.cwd())
    bootstrap_p.add_argument("--query", default=None)

    pull_p = sub.add_parser("pull", help="Pull context for a query (approval gated by default)")
    pull_p.add_argument("query")
    pull_p.add_argument("--approve", action="store_true")
    pull_p.add_argument("--limit", type=int, default=3)

    organize_p = sub.add_parser("organize", help="Copy .srec files into ~/.spiral/coils/")
    organize_p.add_argument("source", type=Path)
    organize_p.add_argument("--category", default="Grok")

    close_p = sub.add_parser("close", help="Log a session boundary")
    close_p.add_argument("--title", required=True)
    close_p.add_argument("--coil", default=None)
    close_p.add_argument("--notes", default="")

    sub.add_parser("config-show", help="Print active session-manager config")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    manager = SessionManager()

    if args.command == "index":
        stats = manager.index_all(cwd=args.cwd)
        print(json.dumps(stats, indent=2))
        return 0

    if args.command == "list":
        print(manager.list_coils())
        return 0

    if args.command == "bootstrap":
        print(manager.bootstrap(cwd=args.cwd, query=args.query))
        return 0

    if args.command == "pull":
        print(manager.pull_context(args.query, approve=args.approve, limit=args.limit))
        return 0

    if args.command == "organize":
        moved = manager.organize_inbox(args.source, category=args.category)
        print(json.dumps({"organized": moved}, indent=2))
        return 0

    if args.command == "close":
        print(manager.close_session(args.title, coil_path=args.coil, notes=args.notes))
        return 0

    if args.command == "config-show":
        cfg = ManagerConfig.load()
        print(
            json.dumps(
                {
                    "home": str(cfg.home),
                    "coils_dir": str(cfg.coils_dir),
                    "index_path": str(cfg.index_path),
                    "require_approval": cfg.require_approval,
                    "scan_paths": [str(p) for p in cfg.scan_paths],
                },
                indent=2,
            )
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())