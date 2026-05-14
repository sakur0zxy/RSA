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

    round_group = subcommands.add_parser(
        "round", help="校验研究轮次 archive，不写入正式记录。"
    )
    round_subcommands = round_group.add_subparsers(dest="round_command", required=True)
    round_validate = round_subcommands.add_parser(
        "validate", help="只读校验轮次 README、summary 和声明的可选文件。"
    )
    round_validate.add_argument("round_id", help="轮次目录名，例如 R001_topic。")
    round_complete = round_subcommands.add_parser(
        "complete-check", help="检查轮次是否满足 completed 人工确认条件。"
    )
    round_complete.add_argument("round_id", help="轮次目录名，例如 R001_topic。")
    round_trace = round_subcommands.add_parser(
        "trace", help="生成或刷新 trace_summary.md，不写入正式记录。"
    )
    round_trace.add_argument("round_id", help="轮次目录名，例如 R001_topic。")

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

    map_group = subcommands.add_parser(
        "map", help="校验或生成文献映射建议；validate 只读，propose 不写正式记录。"
    )
    map_subcommands = map_group.add_subparsers(dest="map_command", required=True)
    map_subcommands.add_parser("validate", help="只读校验 literature_map.md。")
    map_propose = map_subcommands.add_parser(
        "propose", help="从轮次 formal_write_requests 生成 map_proposal.md。"
    )
    map_propose.add_argument("--round", required=True, dest="round_id", help="轮次目录名。")

    gap_group = subcommands.add_parser(
        "gap", help="生成或校验 topic profile 的研究空白报告。"
    )
    gap_subcommands = gap_group.add_subparsers(dest="gap_command", required=True)
    gap_generate = gap_subcommands.add_parser(
        "generate", help="生成 01_literature/synthesis 下的 gap report。"
    )
    gap_generate.add_argument("--topic", required=True, help="topic_id 或 profile 路径。")
    gap_validate = gap_subcommands.add_parser(
        "validate", help="只读校验已有 gap report 是否过期。"
    )
    gap_validate.add_argument("--topic", required=True, help="topic_id 或 profile 路径。")

    note_group = subcommands.add_parser(
        "note", help="创建、校验或查看单篇文献 reading note；validate/status 只读。"
    )
    note_subcommands = note_group.add_subparsers(dest="note_command", required=True)
    note_create = note_subcommands.add_parser(
        "create", help="从本地、用户提供或已授权全文创建结构化阅读笔记。"
    )
    note_create.add_argument("paper_id", help="正式文献编号，例如 P001。")
    note_create.add_argument("--source-file", required=True, help="本地全文文件路径。")
    note_create.add_argument(
        "--authorization",
        required=True,
        choices=["provided", "local", "authorized"],
        help="全文授权来源；只能是 provided/local/authorized。",
    )
    note_validate = note_subcommands.add_parser(
        "validate", help="只读校验 P###_reading_note.md 的 schema 和人工确认状态。"
    )
    note_validate.add_argument("paper_id", help="正式文献编号，例如 P001。")
    note_status = note_subcommands.add_parser(
        "status", help="只读查看 reading note 或 PDF 获取状态。"
    )
    note_status.add_argument("paper_id", help="正式文献编号，例如 P001。")

    source_group = subcommands.add_parser(
        "source", help="登记、校验或查看本地/已授权全文来源；validate/status 只读。"
    )
    source_subcommands = source_group.add_subparsers(dest="source_command", required=True)
    source_add = source_subcommands.add_parser(
        "add", help="登记本地、用户提供或已授权来源文件，并写入 source ledger。"
    )
    source_add.add_argument("paper_id", help="正式文献编号，例如 P001。")
    source_add.add_argument("--source-file", required=True, help="本地来源文件路径。")
    source_add.add_argument(
        "--authorization",
        required=True,
        choices=["provided", "local", "authorized", "open_access", "user_authorized"],
        help="来源授权方式。不会绕过 paywall 或访问控制。",
    )
    source_add.add_argument(
        "--source-type",
        default="pdf",
        choices=["pdf", "supplement", "dataset", "web_page", "other"],
        help="来源类型；默认 pdf。",
    )
    source_add.add_argument("--source-url", help="可选来源 URL。")
    source_add.add_argument(
        "--license-note",
        required=True,
        help="中文授权或来源说明，说明为什么可以本地保存/阅读。",
    )
    source_add.add_argument("--added-by", help="添加人。")
    source_validate = source_subcommands.add_parser(
        "validate", help="只读校验 source ledger 和本地来源文件。"
    )
    source_validate.add_argument("paper_id", help="正式文献编号，例如 P001。")
    source_status = source_subcommands.add_parser(
        "status", help="只读查看 source ledger 状态。"
    )
    source_status.add_argument("paper_id", help="正式文献编号，例如 P001。")
    source_find = source_subcommands.add_parser(
        "find",
        help="自动发现、审查并默认下载规则允许的授权全文来源。",
    )
    source_find.add_argument("paper_id", help="正式文献编号，例如 P001。")
    source_find.add_argument(
        "--no-download",
        action="store_true",
        help="只生成候选来源，不执行自动下载。",
    )
    source_find.add_argument("--provider", help="只使用指定 provider_id。")
    source_find.add_argument("--max-results", type=int, help="候选来源数量上限。")
    source_candidates = source_subcommands.add_parser(
        "candidates", help="只读查看 source candidate 审查状态。"
    )
    source_candidates.add_argument("paper_id", help="正式文献编号，例如 P001。")
    source_download = source_subcommands.add_parser(
        "download", help="下载已审查通过的候选来源，或显式下载授权 URL。"
    )
    source_download.add_argument("paper_id", help="正式文献编号，例如 P001。")
    download_target = source_download.add_mutually_exclusive_group(required=True)
    download_target.add_argument("--best", action="store_true", help="下载最佳已批准候选。")
    download_target.add_argument("--candidate", help="下载指定候选编号，例如 SC001。")
    download_target.add_argument("--url", help="显式授权的 PDF URL 或 file:// 路径。")
    source_download.add_argument(
        "--authorization-mode",
        choices=[
            "open_access",
            "direct_access",
            "user_authorized_access",
            "institutional_subscription",
            "personal_subscription",
            "provided",
            "local",
        ],
        help="手动 URL 下载的授权模式。",
    )
    source_download.add_argument(
        "--access-mode",
        choices=[
            "open_access",
            "direct_access",
            "user_authorized_access",
            "institutional_subscription",
            "personal_subscription",
            "provided",
            "local",
        ],
        help="手动 URL 下载的访问方式。",
    )
    source_download.add_argument(
        "--usage-restriction-zh",
        help="中文使用限制，例如仅供个人科研阅读，不得公开分发 PDF。",
    )
    source_download.add_argument(
        "--authorization-basis-zh",
        help="中文授权依据说明；缺省时记录为用户显式提供授权 URL。",
    )
    source_download.add_argument(
        "--provider-id",
        default="manual_url",
        help="手动 URL 对应的 provider_id；默认 manual_url。",
    )
    source_download.add_argument(
        "--version-label",
        default="publisher_version",
        help="PDF 版本标签，例如 publisher_version、repository_copy、arxiv_preprint。",
    )

    asset_group = subcommands.add_parser(
        "asset", help="登记、校验或查看截图/图表/结果图资产；validate/status 只读。"
    )
    asset_subcommands = asset_group.add_subparsers(dest="asset_command", required=True)
    asset_add = asset_subcommands.add_parser(
        "add", help="登记本地截图、图表、结果图或补充资产，并写入 manifest。"
    )
    asset_add.add_argument("paper_id", help="正式文献编号，例如 P001。")
    asset_add.add_argument("--file", required=True, dest="asset_file", help="本地资产文件路径。")
    asset_add.add_argument(
        "--kind",
        required=True,
        choices=["figure", "table", "result", "screenshot", "supplement", "other"],
        help="资产类型。",
    )
    asset_add.add_argument("--label", help="人类可读标签，例如 Fig. 3。")
    asset_add.add_argument("--description-zh", help="中文说明，记录该资产为什么重要。")
    asset_add.add_argument("--page", help="可选页码。")
    asset_add.add_argument("--figure", help="可选图号、表号或结果编号。")
    asset_add.add_argument("--added-by", help="添加人。")
    asset_validate = asset_subcommands.add_parser(
        "validate", help="只读校验 asset manifest 和本地资产文件。"
    )
    asset_validate.add_argument("paper_id", help="正式文献编号，例如 P001。")
    asset_status = asset_subcommands.add_parser(
        "status", help="只读查看 asset manifest 状态。"
    )
    asset_status.add_argument("paper_id", help="正式文献编号，例如 P001。")

    eval_group = subcommands.add_parser(
        "eval", help="运行本地 harness eval fixtures、baseline 和回归比较。"
    )
    eval_subcommands = eval_group.add_subparsers(dest="eval_command", required=True)
    eval_subcommands.add_parser("run", help="运行全部本地 eval fixtures 并写入 eval_report.md。")
    eval_subcommands.add_parser(
        "baseline", help="运行 eval fixtures 并写入 eval_baseline.yaml。"
    )
    eval_subcommands.add_parser(
        "compare", help="将当前 eval fixtures 与 baseline 比较并写入 regression report。"
    )

    formal_group = subcommands.add_parser(
        "formal", help="正式记录写入命令；所有写入都需要人工确认。"
    )
    formal_subcommands = formal_group.add_subparsers(dest="formal_command", required=True)
    apply_map = formal_subcommands.add_parser(
        "apply-map", help="唯一的 Phase 3 正式 literature_map.md 写入路径。"
    )
    apply_map.add_argument("--source-round", required=True, help="来源轮次目录名。")
    apply_map.add_argument(
        "--human-confirmed",
        action="store_true",
        help="确认执行正式写入；缺少时不会修改正式记录。",
    )
    apply_map.add_argument("--confirmed-by", help="人工确认人。")
    apply_map.add_argument("--confirmed-at", help="人工确认时间，可选。")
    apply_note = formal_subcommands.add_parser(
        "apply-note", help="将 approved reading note 的请求写入正式 map 或研究笔记。"
    )
    apply_note.add_argument("--source-note", required=True, help="来源阅读笔记的 paper_id，例如 P001。")
    apply_note.add_argument(
        "--human-confirmed",
        action="store_true",
        help="确认执行正式写入；缺少时不会修改正式记录。",
    )
    apply_note.add_argument("--confirmed-by", help="人工确认人。")
    apply_note.add_argument("--confirmed-at", help="人工确认时间，可选。")
    return parser


def _run_init(root: Path) -> int:
    from .skeleton import create_literature_skeleton

    config = load_project_config(root)
    result = create_literature_skeleton(config)
    print(
        "已初始化文献基础: "
        f"新建 {result.created_count} 项，已有 {result.existing_count} 项"
    )
    return 0


def _run_validate_profile(profile_path: Path) -> int:
    from .profiles import validate_topic_profile

    errors = validate_topic_profile(profile_path)
    if errors:
        print(f"profile 无效: {profile_path}", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    print(f"profile 有效: {profile_path}")
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
        print(f"创建调研轮次失败: {exc}", file=sys.stderr)
        return 1
    print(f"已创建调研轮次 {result.round_id}: {result.path}")
    return 0


def _print_round_validation(result, *, completion_check: bool) -> int:
    if result.errors:
        title = "轮次完成检查未通过" if completion_check else "轮次校验未通过"
        print(f"{title}: {result.round_id}", file=sys.stderr)
        for error in result.errors:
            print(f"- {error}", file=sys.stderr)
        return 1
    if completion_check:
        print(f"轮次可以标记为 completed: {result.round_id}")
    else:
        print(f"轮次 archive 有效: {result.round_id} (status: {result.status})")
    return 0


def _run_round_command(args: argparse.Namespace, root: Path) -> int:
    from .rounds import validate_round_archive

    config = load_project_config(root)
    if args.round_command == "trace":
        from .trace import TraceError, write_trace_summary

        try:
            result = write_trace_summary(config, args.round_id)
        except TraceError as exc:
            print(f"Trace summary 生成失败: {exc}", file=sys.stderr)
            return 1
        print(f"已生成 trace summary: {result.path}")
        return 0
    completion_check = args.round_command == "complete-check"
    result = validate_round_archive(
        config,
        args.round_id,
        completion_check=completion_check,
    )
    return _print_round_validation(result, completion_check=completion_check)


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


def _run_map_command(args: argparse.Namespace, root: Path) -> int:
    from .map import MapError, validate_literature_map, write_map_proposal

    config = load_project_config(root)
    try:
        if args.map_command == "validate":
            errors = validate_literature_map(config)
            if errors:
                for error in errors:
                    print(f"文献映射无效: {error}", file=sys.stderr)
                return 1
            print(f"文献映射有效: {config.literature_map_path}")
            return 0
        if args.map_command == "propose":
            path = write_map_proposal(config, args.round_id)
            print(f"已生成文献映射建议: {path}；正式写入请运行 rsa formal apply-map。")
            return 0
    except MapError as exc:
        print(f"文献映射操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_gap_command(args: argparse.Namespace, root: Path) -> int:
    from .map import MapError, generate_gap_report, validate_gap_report

    config = load_project_config(root)
    try:
        if args.gap_command == "generate":
            path, _report = generate_gap_report(config, args.topic)
            print(f"已生成研究空白报告: {path}")
            return 0
        if args.gap_command == "validate":
            errors = validate_gap_report(config, args.topic)
            if errors:
                for error in errors:
                    print(f"研究空白报告不一致: {error}", file=sys.stderr)
                return 1
            print(f"研究空白报告一致: {args.topic}")
            return 0
    except MapError as exc:
        print(f"研究空白报告操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_note_command(args: argparse.Namespace, root: Path) -> int:
    from .notes import NoteError, create_reading_note, note_status, validate_reading_note

    config = load_project_config(root)
    try:
        if args.note_command == "create":
            result = create_reading_note(
                config,
                args.paper_id,
                source_file=args.source_file,
                authorization=args.authorization,
            )
            print(f"已创建阅读笔记: {result.path}")
            return 0
        if args.note_command == "validate":
            errors = validate_reading_note(config, args.paper_id)
            if errors:
                for error in errors:
                    print(f"阅读笔记无效: {error}", file=sys.stderr)
                return 1
            print(f"阅读笔记有效: {args.paper_id}")
            return 0
        if args.note_command == "status":
            print(f"阅读笔记状态: {args.paper_id} -> {note_status(config, args.paper_id)}")
            return 0
    except NoteError as exc:
        print(f"阅读笔记操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_source_command(args: argparse.Namespace, root: Path) -> int:
    from .assets import (
        AssetError,
        add_source_record,
        source_status,
        validate_source_record,
    )
    from .acquisition import (
        AcquisitionError,
        candidate_status,
        download_best_candidate,
        download_candidate,
        download_direct_url,
        find_sources,
        load_candidate_record,
    )

    config = load_project_config(root)
    try:
        if args.source_command == "add":
            result = add_source_record(
                config,
                args.paper_id,
                source_file=args.source_file,
                authorization=args.authorization,
                source_type=args.source_type,
                source_url=args.source_url,
                license_note=args.license_note,
                added_by=args.added_by,
            )
            print(
                f"已登记来源 {result.source_id}: {result.local_path}；ledger: {result.record_path}"
            )
            return 0
        if args.source_command == "validate":
            errors = validate_source_record(config, args.paper_id)
            if errors:
                for error in errors:
                    print(f"来源记录无效: {error}", file=sys.stderr)
                return 1
            print(f"来源记录有效: {args.paper_id}")
            return 0
        if args.source_command == "status":
            status = source_status(config, args.paper_id)
            candidates = candidate_status(config, args.paper_id)
            print(
                f"来源状态: {args.paper_id} -> 总数={status.total_count}, "
                f"可用={status.available_count}, 阻塞={status.blocked_count}; "
                f"候选={candidates.total_count}, 已批准={candidates.approved_count}, "
                f"已下载={candidates.downloaded_count}, 重复={candidates.duplicate_count}, "
                f"失败={candidates.failed_count}; ledger={status.path}; "
                f"candidates={candidates.path}"
            )
            return 0
        if args.source_command == "find":
            result = find_sources(
                config,
                args.paper_id,
                auto_download=not args.no_download,
                provider_filter=args.provider,
                max_results=args.max_results,
            )
            mode = "仅生成候选" if args.no_download else "monitored_auto 自动审查/下载"
            print(
                f"来源发现完成: {args.paper_id} ({mode}) -> "
                f"候选={result.candidates_found}, 已批准={result.approved_count}, "
                f"已下载={result.downloaded_count}, 重复={result.duplicate_count}, "
                f"阻塞={result.blocked_count}, 失败={result.failed_count}; "
                f"记录={result.path}"
            )
            return 0
        if args.source_command == "candidates":
            record = load_candidate_record(config, args.paper_id)
            candidates = record.get("candidates") if isinstance(record.get("candidates"), list) else []
            print(f"候选来源: {args.paper_id} -> {len(candidates)} 项")
            for item in candidates:
                if not isinstance(item, dict):
                    continue
                print(
                    "- "
                    f"{item.get('candidate_id')} | provider={item.get('provider_id')} | "
                    f"status={item.get('status')} | match_basis={item.get('match_basis')} | "
                    f"authorization_mode={item.get('authorization_mode')} | "
                    f"access_mode={item.get('access_mode')} | "
                    f"reason={item.get('reason_zh')} | local_path={item.get('local_path')}"
                )
            return 0
        if args.source_command == "download":
            if args.best:
                result = download_best_candidate(config, args.paper_id)
            elif args.candidate:
                result = download_candidate(config, args.paper_id, args.candidate)
            else:
                result = download_direct_url(
                    config,
                    args.paper_id,
                    url=args.url,
                    authorization_mode=args.authorization_mode,
                    access_mode=args.access_mode,
                    usage_restriction_zh=args.usage_restriction_zh,
                    authorization_basis_zh=args.authorization_basis_zh,
                    provider_id=args.provider_id,
                    version_label=args.version_label,
                )
            print(
                f"来源下载完成: {args.paper_id} {result.candidate_id} -> "
                f"status={result.status}, source_id={result.source_id}, "
                f"local_path={result.local_path}; {result.reason_zh}"
            )
            return 0
    except (AssetError, AcquisitionError) as exc:
        print(f"来源操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_asset_command(args: argparse.Namespace, root: Path) -> int:
    from .assets import (
        AssetError,
        add_asset_record,
        asset_status,
        validate_asset_manifest,
    )

    config = load_project_config(root)
    try:
        if args.asset_command == "add":
            result = add_asset_record(
                config,
                args.paper_id,
                asset_file=args.asset_file,
                kind=args.kind,
                label=args.label,
                description_zh=args.description_zh,
                page=args.page,
                figure=args.figure,
                added_by=args.added_by,
            )
            print(
                f"已登记资产 {result.asset_id}: {result.local_path}；manifest: {result.manifest_path}"
            )
            return 0
        if args.asset_command == "validate":
            errors = validate_asset_manifest(config, args.paper_id)
            if errors:
                for error in errors:
                    print(f"资产记录无效: {error}", file=sys.stderr)
                return 1
            print(f"资产记录有效: {args.paper_id}")
            return 0
        if args.asset_command == "status":
            status = asset_status(config, args.paper_id)
            print(
                f"资产状态: {args.paper_id} -> 总数={status.total_count}, "
                f"可用={status.available_count}; manifest={status.path}"
            )
            return 0
    except AssetError as exc:
        print(f"资产操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_eval_command(args: argparse.Namespace, root: Path) -> int:
    from .evals import (
        EvalError,
        compare_eval_baseline,
        run_eval_fixtures,
        write_eval_baseline,
        write_eval_report,
    )

    config = load_project_config(root)
    if args.eval_command == "run":
        result = run_eval_fixtures()
        path = write_eval_report(config, result)
        print(
            f"Eval 完成: 通过 {result.passed_count}/{len(result.cases)}；报告: {path}"
        )
        return 0 if result.passed else 1
    if args.eval_command == "baseline":
        result = run_eval_fixtures()
        path = write_eval_baseline(config, result)
        write_eval_report(config, result)
        print(f"Eval baseline 已写入: {path}")
        return 0 if result.passed else 1
    if args.eval_command == "compare":
        try:
            result = compare_eval_baseline(config)
        except EvalError as exc:
            print(f"Eval compare 失败: {exc}", file=sys.stderr)
            return 1
        print(
            f"Eval compare 完成: 回归数={len(result.regressions)}；报告: {result.path}"
        )
        return 0 if result.passed else 1
    return 2


def _run_formal_command(args: argparse.Namespace, root: Path) -> int:
    from .formal import FormalWriteError, apply_map_requests, apply_note_requests

    config = load_project_config(root)
    if args.formal_command == "apply-map":
        try:
            result = apply_map_requests(
                config,
                args.source_round,
                human_confirmed=args.human_confirmed,
                confirmed_by=args.confirmed_by,
                confirmed_at=args.confirmed_at,
            )
        except FormalWriteError as exc:
            print(f"正式写入被阻止: {exc}", file=sys.stderr)
            return 1
        print(
            "正式映射写入完成: "
            f"已追加 {result.applied_count} 行 -> {result.destination}; "
            f"已跳过 add_metadata 请求 {result.skipped_metadata_count} 个"
        )
        return 0
    if args.formal_command == "apply-note":
        try:
            result = apply_note_requests(
                config,
                args.source_note,
                human_confirmed=args.human_confirmed,
                confirmed_by=args.confirmed_by,
                confirmed_at=args.confirmed_at,
            )
        except FormalWriteError as exc:
            print(f"正式写入被阻止: {exc}", file=sys.stderr)
            return 1
        print(
            "正式阅读笔记写入完成: "
            f"文献映射行 {result.map_rows_applied} -> {result.map_destination}; "
            f"研究笔记行 {result.research_notes_applied} -> {result.research_notes_destination}"
        )
        return 0
    return 2


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
        if args.command == "round":
            return _run_round_command(args, root)
        if args.command == "validate-metadata":
            return _run_validate_metadata(Path(args.metadata))
        if args.command == "add-paper":
            return _run_add_paper(args, root)
        if args.command == "validate-index":
            return _run_validate_index(root)
        if args.command == "regenerate-index":
            return _run_regenerate_index(root)
        if args.command == "map":
            return _run_map_command(args, root)
        if args.command == "gap":
            return _run_gap_command(args, root)
        if args.command == "note":
            return _run_note_command(args, root)
        if args.command == "source":
            return _run_source_command(args, root)
        if args.command == "asset":
            return _run_asset_command(args, root)
        if args.command == "eval":
            return _run_eval_command(args, root)
        if args.command == "formal":
            return _run_formal_command(args, root)
    except ConfigError as exc:
        print(f"配置错误: {exc}", file=sys.stderr)
        return 2

    parser.error(f"unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
