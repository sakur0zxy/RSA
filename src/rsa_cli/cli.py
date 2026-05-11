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
    validate_profile = subcommands.add_parser(
        "validate-profile", help="Validate a topic profile YAML file."
    )
    validate_profile.add_argument("profile", help="Path to the topic profile YAML file.")
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


def _run_validate_profile(profile_path: Path) -> int:
    from .profiles import validate_topic_profile

    errors = validate_topic_profile(profile_path)
    if errors:
        print(f"Profile invalid: {profile_path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Profile valid: {profile_path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    root = Path(args.root)
    try:
        if args.command == "init":
            return _run_init(root)
        if args.command == "validate-profile":
            return _run_validate_profile(Path(args.profile))
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
