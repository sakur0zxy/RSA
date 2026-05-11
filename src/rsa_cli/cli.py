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
    new_round = subcommands.add_parser(
        "new-round", help="Create a bounded research round archive."
    )
    new_round.add_argument("--topic", required=True, help="Topic profile YAML path.")
    new_round.add_argument("--objective", required=True, help="Round objective.")
    new_round.add_argument("--name", required=True, help="Short round name.")
    new_round.add_argument("--max-candidates", type=int, help="Candidate paper limit.")
    new_round.add_argument(
        "--allowed-tool",
        action="append",
        dest="allowed_tools",
        help="Allowed tool for this round. May be repeated.",
    )
    new_round.add_argument("--output-policy", help="Round output policy.")
    new_round.add_argument("--approval-mode", help="Human approval mode.")
    new_round.add_argument("--campaign-id", help="Optional campaign identifier.")
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


def _run_new_round(args: argparse.Namespace, root: Path) -> int:
    from .rounds import RoundError, create_research_round

    config = load_project_config(root)
    topic_path = Path(args.topic)
    if not topic_path.is_absolute():
        topic_path = config.root / topic_path
    try:
        result = create_research_round(
            config=config,
            topic_profile_path=topic_path,
            objective=args.objective,
            name=args.name,
            max_candidates=args.max_candidates,
            allowed_tools=args.allowed_tools,
            output_policy=args.output_policy,
            approval_mode=args.approval_mode,
            campaign_id=args.campaign_id,
        )
    except RoundError as exc:
        print(f"Round error: {exc}", file=sys.stderr)
        return 1
    print(f"Created round {result.round_id}: {result.path}")
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
        if args.command == "new-round":
            return _run_new_round(args, root)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
