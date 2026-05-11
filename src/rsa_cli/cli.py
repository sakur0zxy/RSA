from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .config import ConfigError, load_project_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="rsa",
        description="RSA 本地科研 agent harness 命令行工具。",
    )
    parser.add_argument(
        "--root",
        default=".",
        help="项目根目录，包含 rsa.yaml；默认使用当前目录。",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("init", help="创建配置好的文献工作区基础结构。")
    validate_profile = subcommands.add_parser(
        "validate-profile", help="校验 topic profile YAML 文件。"
    )
    validate_profile.add_argument("profile", help="topic profile YAML 文件路径。")
    new_round = subcommands.add_parser(
        "new-round", help="创建一个有边界的文献调研轮次归档。"
    )
    new_round.add_argument("--topic", required=True, help="topic profile YAML 路径。")
    new_round.add_argument("--objective", required=True, help="本轮调研目标。")
    new_round.add_argument("--name", required=True, help="本轮短名称。")
    new_round.add_argument("--max-candidates", type=int, help="候选文献数量上限。")
    new_round.add_argument(
        "--allowed-tool",
        action="append",
        dest="allowed_tools",
        help="本轮允许使用的工具；可重复传入。",
    )
    new_round.add_argument("--output-policy", help="本轮输出策略。")
    new_round.add_argument("--approval-mode", help="人工确认模式。")
    new_round.add_argument("--campaign-id", help="可选 campaign 标识。")

    validate_metadata = subcommands.add_parser(
        "validate-metadata", help="校验正式 metadata/P###.yaml 文件。"
    )
    validate_metadata.add_argument("metadata", help="metadata/P###.yaml 文件路径。")

    add_paper = subcommands.add_parser(
        "add-paper", help="通过人工确认门禁写入正式 metadata/P###.yaml。"
    )
    add_paper.add_argument("--title", required=True, help="论文标题。")
    add_paper.add_argument(
        "--author", action="append", dest="authors", required=True, help="作者；可重复传入。"
    )
    add_paper.add_argument("--year", required=True, help="发表年份。")
    add_paper.add_argument("--venue", required=True, help="期刊、会议或预印本平台。")
    add_paper.add_argument("--doi", help="DOI；与 --official-url 至少提供一个。")
    add_paper.add_argument(
        "--official-url", dest="official_url", help="官方页面或可靠来源链接。"
    )
    add_paper.add_argument(
        "--source-reliability", required=True, help="来源可靠性说明。"
    )
    add_paper.add_argument("--decision", required=True, help="人工收录决策。")
    add_paper.add_argument("--decision-reason", required=True, help="收录决策原因。")
    add_paper.add_argument("--last-checked", required=True, help="最近一次核验时间。")
    add_paper.add_argument("--pdf-status", required=True, help="PDF 获取与授权状态。")
    add_paper.add_argument("--local-pdf", help="本地 PDF 路径。")
    add_paper.add_argument(
        "--asset", action="append", dest="assets", help="本地截图、图表或结果资产路径。"
    )
    add_paper.add_argument("--topic-profile", help="关联 topic profile。")
    add_paper.add_argument(
        "--priority-question",
        action="append",
        dest="priority_questions",
        help="该文献服务的优先问题；可重复传入。",
    )
    add_paper.add_argument(
        "--used-for", action="append", dest="used_for", help="计划用途；可重复传入。"
    )
    add_paper.add_argument(
        "--research-role",
        action="append",
        dest="research_roles",
        help="研究角色；可重复传入。",
    )
    add_paper.add_argument("--notes", help="人工备注。")
    add_paper.add_argument(
        "--human-confirmed",
        action="store_true",
        help="显式确认写入正式记录；未提供时不会创建 metadata/P###.yaml。",
    )
    add_paper.add_argument("--confirmed-by", help="人工确认人。")
    add_paper.add_argument("--confirmed-at", help="人工确认时间；缺省为当天日期。")

    subcommands.add_parser("validate-index", help="校验 paper_index.md 是否与 metadata 一致。")
    subcommands.add_parser("regenerate-index", help="根据 metadata 显式重建 paper_index.md。")
    return parser


def _run_init(root: Path) -> int:
    from .skeleton import create_literature_skeleton

    config = load_project_config(root)
    result = create_literature_skeleton(config)
    print(
        "已初始化文献基础 / Initialized literature foundation: "
        f"{result.created_count} created, {result.existing_count} existing"
    )
    return 0


def _run_validate_profile(profile_path: Path) -> int:
    from .profiles import validate_topic_profile

    errors = validate_topic_profile(profile_path)
    if errors:
        print(f"Profile invalid / profile 无效: {profile_path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"Profile valid / profile 有效: {profile_path}")
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
    print(f"已创建调研轮次 / Created round {result.round_id}: {result.path}")
    return 0


def _run_validate_metadata(metadata_path: Path) -> int:
    from .metadata import validate_metadata_record

    errors = validate_metadata_record(metadata_path)
    if errors:
        print(f"元数据无效: {metadata_path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"元数据有效: {metadata_path}")
    return 0


def _run_add_paper(args: argparse.Namespace, root: Path) -> int:
    from .metadata import MetadataError, write_metadata_record

    config = load_project_config(root)
    values = {
        "title": args.title,
        "authors": args.authors,
        "year": args.year,
        "venue": args.venue,
        "doi": args.doi,
        "official_url": args.official_url,
        "source_reliability": args.source_reliability,
        "decision": args.decision,
        "decision_reason": args.decision_reason,
        "last_checked": args.last_checked,
        "pdf_status": args.pdf_status,
        "local_pdf": args.local_pdf,
        "assets": args.assets,
        "topic_profile": args.topic_profile,
        "priority_questions": args.priority_questions,
        "used_for": args.used_for,
        "research_roles": args.research_roles,
        "notes": args.notes,
    }
    try:
        path = write_metadata_record(
            config=config,
            values=values,
            human_confirmed=args.human_confirmed,
            confirmed_by=args.confirmed_by,
            confirmed_at=args.confirmed_at,
        )
    except MetadataError as exc:
        print(f"无法写入正式元数据: {exc}", file=sys.stderr)
        return 1
    print(f"已写入正式文献 {path.stem}: {path}")
    return 0


def _run_validate_index(root: Path) -> int:
    from .index import IndexError, validate_paper_index

    config = load_project_config(root)
    try:
        errors = validate_paper_index(config)
    except IndexError as exc:
        print(f"索引校验失败: {exc}", file=sys.stderr)
        return 1
    if errors:
        for error in errors:
            print(f"索引不一致: {error}", file=sys.stderr)
        return 1
    print(f"索引一致: {config.paper_index_path}")
    return 0


def _run_regenerate_index(root: Path) -> int:
    from .index import IndexError, regenerate_paper_index

    config = load_project_config(root)
    try:
        path = regenerate_paper_index(config)
    except IndexError as exc:
        print(f"无法重建索引: {exc}", file=sys.stderr)
        return 1
    print(f"已重建文献索引: {path}")
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
        if args.command == "validate-metadata":
            return _run_validate_metadata(Path(args.metadata))
        if args.command == "add-paper":
            return _run_add_paper(args, root)
        if args.command == "validate-index":
            return _run_validate_index(root)
        if args.command == "regenerate-index":
            return _run_regenerate_index(root)
    except ConfigError as exc:
        print(f"Configuration error / 配置错误: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
