from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .config import ConfigError, load_project_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="rsa")
    parser.add_argument(
        "--root",
        default=".",
        help="Project root containing rsa.yaml. Defaults to the current directory.",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init", help="Create the configured literature foundation.")
    return parser


def _run_init(root: Path) -> int:
    from .skeleton import create_literature_skeleton

    config = load_project_config(root)
    result = create_literature_skeleton(config)
    print(
        "Initialized literature foundation: "
        f"{result.created_count} created, {result.existing_count} existing"
    )
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        if args.command == "init":
            return _run_init(root)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
