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
    note_draft = note_subcommands.add_parser(
        "draft",
        help="基于本地/用户提供/已授权全文自动生成中文 reading note draft 和 review packet。",
    )
    note_draft.add_argument("paper_id", help="正式文献编号，例如 P001。")
    note_draft.add_argument(
        "--source-file",
        help="可选：临时指定本地全文文件；缺省时从 sources/P###.yaml 选择可用 PDF。",
    )
    note_draft.add_argument(
        "--overwrite-draft",
        action="store_true",
        help="只允许覆盖已有 note_status: draft 的阅读笔记；不会覆盖 ready_for_review/approved。",
    )
    note_draft.add_argument(
        "--retry",
        action="store_true",
        help="模型输出 schema 不合格时允许一次安全重试。",
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
    source_login = source_subcommands.add_parser(
        "login", help="打开 browser_session provider 登录页，并保存本地授权 session。"
    )
    source_login.add_argument("provider_id", help="browser_session provider_id。")
    source_login.add_argument(
        "--headless",
        action="store_true",
        help="无头浏览器模式；通常只用于自动化测试，并需要 --wait-seconds。",
    )
    source_login.add_argument(
        "--wait-seconds",
        type=int,
        help="打开登录页后等待的秒数；未提供时会等待用户按 Enter。",
    )
    source_session = source_subcommands.add_parser(
        "session", help="查看或清除 browser_session 本地会话；不修改正式记录。"
    )
    session_subcommands = source_session.add_subparsers(
        dest="session_command", required=True
    )
    session_status = session_subcommands.add_parser(
        "status", help="只读查看 browser_session 是否已登录和本地 session 状态。"
    )
    session_status.add_argument("provider_id", help="browser_session provider_id。")
    session_clear = session_subcommands.add_parser(
        "clear", help="删除指定 provider 的本地 browser session 文件。"
    )
    session_clear.add_argument("provider_id", help="browser_session provider_id。")
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

    visual_group = subcommands.add_parser(
        "visual",
        help="提取、校验或查看论文图表/表格视觉证据候选；validate/status 只读。",
    )
    visual_subcommands = visual_group.add_subparsers(
        dest="visual_command", required=True
    )
    visual_extract = visual_subcommands.add_parser(
        "extract",
        help="从已授权/本地 PDF 生成视觉证据候选、裁图和本地上下文包；不写入正式记录。",
    )
    visual_extract.add_argument("paper_id", help="正式文献编号，例如 P001。")
    visual_extract.add_argument(
        "--all-detected",
        action="store_true",
        help="扩展模式：裁取所有检测到的图表/表格候选，可能产生较多候选。",
    )
    visual_extract.add_argument(
        "--pages",
        help="只处理指定页码，例如 3 或 3,5-7。",
    )
    visual_extract.add_argument(
        "--asset-suggestions-only",
        action="store_true",
        help="只把 reading note 的 asset_suggestions 转成候选，不进行全文页扫描。",
    )
    visual_validate = visual_subcommands.add_parser(
        "validate",
        help="只读校验 visual_evidence_candidates.yaml 的 schema、状态和回源链接。",
    )
    visual_validate.add_argument("paper_id", help="正式文献编号，例如 P001。")
    visual_status = visual_subcommands.add_parser(
        "status",
        help="只读查看视觉证据候选数量、降级状态和候选文件路径。",
    )
    visual_status.add_argument("paper_id", help="正式文献编号，例如 P001。")

    campaign_group = subcommands.add_parser(
        "campaign",
        help="创建、导入、校验或查看批量文献候选队列；不执行评分、自动工作流或正式写入。",
    )
    campaign_subcommands = campaign_group.add_subparsers(
        dest="campaign_command", required=True
    )
    campaign_create = campaign_subcommands.add_parser(
        "create",
        help="创建一个批量文献候选 campaign，用于后续导入和队列管理。",
    )
    campaign_create.add_argument("--name-zh", required=True, help="中文 campaign 名称。")
    campaign_create.add_argument("--objective-zh", required=True, help="中文批量任务目标。")
    campaign_create.add_argument("--topic-profile", help="可选 topic profile id。")
    campaign_create.add_argument("--created-by", help="创建人。")
    campaign_import = campaign_subcommands.add_parser(
        "import",
        help="从 CSV/TSV/YAML 导入候选文献条目，执行轻量去重和正式 metadata 链接。",
    )
    campaign_import.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_import.add_argument("--file", required=True, dest="source_file", help="CSV/TSV/YAML 导入文件。")
    campaign_import.add_argument(
        "--no-dedup",
        action="store_true",
        help="关闭 campaign 内部去重；默认会按 DOI、URL 或 title/year/author 去重。",
    )
    campaign_validate = campaign_subcommands.add_parser(
        "validate",
        help="只读校验 campaign YAML 的 schema、去重键、状态和回源字段。",
    )
    campaign_validate.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_status = campaign_subcommands.add_parser(
        "status",
        help="只读查看 campaign 队列数量、重复项、已链接项和阻塞项。",
    )
    campaign_status.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_run = campaign_subcommands.add_parser(
        "run",
        help="按阶段队列限流运行 campaign；自动产物进入 staging/review，不绕过 formal gate。",
    )
    campaign_run.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_run.add_argument("--dry-run", action="store_true", help="只生成运行计划和监管队列，不实际运行单篇 workflow。")
    campaign_run.add_argument("--item", "--items", action="append", dest="item_ids", help="只处理指定 campaign item，可重复传入。")
    campaign_run.add_argument("--status", action="append", dest="status_filter", help="只处理指定 item status，可重复传入。")
    campaign_run.add_argument("--max-acquisition", type=int, help="覆盖 acquisition 阶段并发上限。")
    campaign_run.add_argument("--max-reading-draft", type=int, help="覆盖 reading draft 阶段并发上限。")
    campaign_run.add_argument("--max-visual", type=int, help="覆盖 visual extraction 阶段并发上限。")
    campaign_run.add_argument("--max-scoring", type=int, help="覆盖 scoring 阶段并发上限。")
    campaign_resume = campaign_subcommands.add_parser(
        "resume",
        help="从 campaign run ledger 恢复未完成项；已完成项不会重复执行。",
    )
    campaign_resume.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_resume.add_argument("--item", "--items", action="append", dest="item_ids", help="只恢复指定 campaign item，可重复传入。")
    campaign_resume.add_argument("--status", action="append", dest="status_filter", help="只恢复指定 item status，可重复传入。")
    campaign_pause = campaign_subcommands.add_parser(
        "pause",
        help="暂停 campaign run，并写入中文暂停原因。",
    )
    campaign_pause.add_argument("campaign_id", help="campaign 编号，例如 C001。")
    campaign_pause.add_argument("--reason", help="中文暂停原因。")
    campaign_queue = campaign_subcommands.add_parser(
        "queue",
        help="生成或查看 review queue；也支持 queue review C001 --item QI001 --decision accepted。",
    )
    campaign_queue.add_argument("first", help="campaign_id，或固定写 review。")
    campaign_queue.add_argument("second", nargs="?", help="当 first=review 时，这里是 campaign_id。")
    campaign_queue.add_argument("--item", dest="queue_item_id", help="要标记的 review queue item，例如 QI001。")
    campaign_queue.add_argument(
        "--decision",
        choices=["accepted", "deferred", "rejected", "needs_followup"],
        help="监管队列决策；不等于 formal approval。",
    )
    campaign_queue.add_argument("--reviewer", help="监管人。")
    campaign_queue.add_argument("--reason", help="中文监管原因。")
    campaign_report = campaign_subcommands.add_parser(
        "report",
        help="生成 campaign 中文批量报告，汇总自动化状态、监管队列和正式写入边界。",
    )
    campaign_report.add_argument("campaign_id", help="campaign 编号，例如 C001。")

    score_group = subcommands.add_parser(
        "score",
        help="生成、校验或监管 Phase 9 AI 辅助评分；评分只进入 staging/review，不写正式记录。",
    )
    score_group.add_argument(
        "score_command",
        nargs="?",
        help="paper_id，或 validate/status/campaign/review。",
    )
    score_group.add_argument(
        "score_target",
        nargs="?",
        help="paper_id 或 campaign_id；例如 P001 或 C001。",
    )
    score_group.add_argument(
        "--overwrite",
        action="store_true",
        help="重新生成 scoring YAML 和 review packet；不会覆盖 review_history。",
    )
    score_group.add_argument(
        "--final-decision",
        choices=["approved", "rejected", "deferred"],
        help="人工监管最终决定；仅用于 rsa score review，不是正式写入批准。",
    )
    score_group.add_argument(
        "--reviewer",
        help="人工监管人；用于 rsa score review。",
    )
    score_group.add_argument(
        "--reason",
        help="中文人工监管原因；用于 rsa score review。",
    )

    workflow_group = subcommands.add_parser(
        "workflow",
        help="运行、恢复、停止或查看单篇论文自动工作流；Phase 10 只处理 P###，不做 campaign 批量调度。",
    )
    workflow_subcommands = workflow_group.add_subparsers(
        dest="workflow_command", required=True
    )
    workflow_run = workflow_subcommands.add_parser(
        "run",
        help="按 acquisition -> reading_draft -> visual_extraction -> scoring -> review_packet 顺序自动处理单篇论文。",
    )
    workflow_run.add_argument("paper_id", help="正式文献编号，例如 P001；不能传入 C### campaign。")
    workflow_run.add_argument("--campaign-id", help="可选 campaign 上下文，例如 C001；不启动批量调度。")
    workflow_run.add_argument("--campaign-item-id", help="可选 campaign item 上下文，例如 CI001。")
    workflow_run.add_argument("--from-step", help="从指定 step 开始本次 run，并跳过之前步骤。")
    workflow_run.add_argument("--skip-acquisition", action="store_true", help="跳过授权获取步骤并记录 skipped。")
    workflow_run.add_argument("--skip-reading-draft", action="store_true", help="跳过阅读草稿步骤并记录 skipped。")
    workflow_run.add_argument("--skip-visual", action="store_true", help="跳过视觉证据候选提取步骤并记录 skipped。")
    workflow_run.add_argument("--skip-scoring", action="store_true", help="跳过 AI 辅助评分步骤并记录 skipped。")

    workflow_resume = workflow_subcommands.add_parser(
        "resume",
        help="从最近一次未完成、失败或可重试步骤恢复单篇 workflow。",
    )
    workflow_resume.add_argument("paper_id", help="正式文献编号，例如 P001。")
    workflow_resume.add_argument("--from-step", help="显式指定恢复位置，例如 scoring。")

    workflow_status = workflow_subcommands.add_parser(
        "status",
        help="只读查看最近一次 workflow run 的状态、当前位置和报告路径。",
    )
    workflow_status.add_argument("paper_id", help="正式文献编号，例如 P001。")

    workflow_report = workflow_subcommands.add_parser(
        "report",
        help="只读显示最近一次 workflow review packet 的路径和摘要。",
    )
    workflow_report.add_argument("paper_id", help="正式文献编号，例如 P001。")

    workflow_stop = workflow_subcommands.add_parser(
        "stop",
        help="把最近一次 workflow 标记为用户暂停；后续不会自动 resume。",
    )
    workflow_stop.add_argument("paper_id", help="正式文献编号，例如 P001。")
    workflow_stop.add_argument("--reason", help="中文暂停原因。")

    workflow_rerun = workflow_subcommands.add_parser(
        "rerun",
        help="从指定 step 重新计算该步骤及后续步骤。",
    )
    workflow_rerun.add_argument("paper_id", help="正式文献编号，例如 P001。")
    workflow_rerun.add_argument("--from-step", required=True, help="重新执行起点，例如 visual_extraction。")

    review_group = subcommands.add_parser(
        "review",
        help="生成、查看、打开或清理本地静态监管台；只展示 staging/review 信息，不写正式记录。",
    )
    review_subcommands = review_group.add_subparsers(dest="review_command", required=True)
    review_build = review_subcommands.add_parser(
        "build",
        help="生成本地 review workspace，可按 campaign 或单篇 paper 聚合证据。",
    )
    review_target = review_build.add_mutually_exclusive_group(required=True)
    review_target.add_argument("--campaign", help="campaign 编号，例如 C001。")
    review_target.add_argument("--paper", help="正式文献编号，例如 P001。")
    review_subcommands.add_parser(
        "status",
        help="只读查看最近生成的 review workspace 目标、统计和 index 路径。",
    )
    review_subcommands.add_parser(
        "open",
        help="打开最近生成的 review workspace index.html；缺失时 fail closed。",
    )
    review_clean = review_subcommands.add_parser(
        "clean",
        help="清理自动生成的 review workspace 页面和 manifest，保留人工记录。",
    )
    review_clean.add_argument(
        "--generated-only",
        action="store_true",
        help="只清理生成文件；Phase 12 当前必须使用该模式。",
    )

    safety_group = subcommands.add_parser(
        "safety",
        help="运行 Phase 13 写作安全、引用链和 campaign failure monitor；只写 safety 审计记录，不写正式记录。",
    )
    safety_subcommands = safety_group.add_subparsers(dest="safety_command", required=True)
    safety_check = safety_subcommands.add_parser(
        "check",
        help="生成单篇论文 claim-level citation safety 记录和中文报告。",
    )
    safety_check.add_argument("paper_id", help="正式文献编号，例如 P001。")
    safety_validate = safety_subcommands.add_parser(
        "validate",
        help="只读校验 P###_safety.yaml，不修改任何文件。",
    )
    safety_validate.add_argument("paper_id", help="正式文献编号，例如 P001。")
    safety_status = safety_subcommands.add_parser(
        "status",
        help="只读查看 P### safety 检查状态。",
    )
    safety_status.add_argument("paper_id", help="正式文献编号，例如 P001。")
    safety_campaign = safety_subcommands.add_parser(
        "campaign",
        help="生成 campaign failure monitor 安全审计记录和中文报告。",
    )
    safety_campaign.add_argument("campaign_id", help="campaign 编号，例如 C001。")

    worker_group = subcommands.add_parser(
        "worker",
        help="运行 Phase 14 本地 worker queue 和定时入队；只调度 staging/review，不执行 formal write。",
    )
    worker_subcommands = worker_group.add_subparsers(dest="worker_command", required=True)
    worker_enqueue = worker_subcommands.add_parser(
        "enqueue",
        help="把一个 campaign/review/safety 任务放入本地 worker queue。",
    )
    worker_enqueue.add_argument(
        "task_type",
        choices=[
            "campaign-run",
            "campaign-resume",
            "campaign-queue",
            "campaign-report",
            "campaign-safety",
            "review-workspace",
        ],
        help="任务类型；会记录为下划线形式，例如 campaign_run。",
    )
    worker_enqueue.add_argument("target_id", help="当前支持 campaign 编号，例如 C001。")
    worker_run = worker_subcommands.add_parser(
        "run",
        help="按队列顺序执行本地 worker 任务；单个失败不会拖死后续任务。",
    )
    worker_run.add_argument("--max-tasks", type=int, help="本次最多处理的 queued 任务数。")
    worker_run.add_argument(
        "--include-due",
        action="store_true",
        help="运行前先把到期 schedule 放入 worker queue。",
    )
    worker_subcommands.add_parser("status", help="只读查看 worker queue 和 schedule 概览。")
    worker_cancel = worker_subcommands.add_parser(
        "cancel", help="取消尚未完成的 worker 任务。"
    )
    worker_cancel.add_argument("task_id", help="worker task 编号，例如 WT001。")
    worker_cancel.add_argument("--reason", help="中文取消原因。")
    worker_recover = worker_subcommands.add_parser(
        "recover", help="把 failed/running/blocked 任务恢复为 queued，等待重试。"
    )
    worker_recover.add_argument("task_id", help="worker task 编号，例如 WT001。")
    worker_recover.add_argument("--reason", help="中文恢复原因。")
    worker_logs = worker_subcommands.add_parser(
        "logs", help="只读查看最近 worker_log.md 摘要。"
    )
    worker_logs.add_argument("--max-lines", type=int, default=20, help="显示最近多少行。")
    worker_schedule = worker_subcommands.add_parser(
        "schedule", help="管理本地定时入队规则；schedule 只入队，不直接执行。"
    )
    worker_schedule_subcommands = worker_schedule.add_subparsers(
        dest="worker_schedule_command", required=True
    )
    worker_schedule_add = worker_schedule_subcommands.add_parser(
        "add", help="新增一个本地 schedule。"
    )
    worker_schedule_add.add_argument(
        "task_type",
        choices=[
            "campaign-run",
            "campaign-resume",
            "campaign-queue",
            "campaign-report",
            "campaign-safety",
            "review-workspace",
        ],
        help="任务类型；会记录为下划线形式，例如 campaign_run。",
    )
    worker_schedule_add.add_argument("target_id", help="当前支持 campaign 编号，例如 C001。")
    worker_schedule_add.add_argument(
        "--interval-hours", required=True, type=int, help="入队间隔小时数，必须为正整数。"
    )
    worker_schedule_add.add_argument("--start-at", help="首次入队时间，ISO 8601 格式。")
    worker_schedule_subcommands.add_parser("list", help="只读列出 schedule。")
    worker_schedule_subcommands.add_parser(
        "due", help="把当前已到期的 schedule 放入 worker queue。"
    )

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
    from .reading_draft import DraftError, draft_reading_note

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
        if args.note_command == "draft":
            result = draft_reading_note(
                config,
                args.paper_id,
                source_file=args.source_file,
                overwrite_draft=args.overwrite_draft,
                retry=args.retry,
            )
            print(
                "已生成自动阅读草稿: "
                f"{result.note_path}; status={result.note_status}; "
                f"score={result.agent_review_score_10}/10; "
                f"review_packet={result.review_packet_path}"
            )
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
    except DraftError as exc:
        print(f"自动阅读草稿生成失败: {exc}", file=sys.stderr)
        return 1
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
    from .browser_session import (
        BrowserSessionError,
        browser_session_status,
        clear_browser_session,
        login_browser_session,
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
        if args.source_command == "login":
            result = login_browser_session(
                config,
                args.provider_id,
                headless=args.headless,
                wait_seconds=args.wait_seconds,
            )
            print(
                f"浏览器会话已保存: provider={result.provider_id}, "
                f"cookies={result.cookie_count}, origins={result.origin_count}; "
                f"session={result.session_path}; metadata={result.metadata_path}"
            )
            return 0
        if args.source_command == "session":
            if args.session_command == "status":
                status = browser_session_status(config, args.provider_id)
                state = "已登录" if status.exists else "未登录"
                print(
                    f"浏览器会话状态: provider={status.provider_id} "
                    f"({status.provider_name_zh}) -> {state}; "
                    f"cookies={status.cookie_count}, origins={status.origin_count}; "
                    f"allowed_domains={','.join(status.allowed_domains)}; "
                    f"session={status.session_path}; updated_at={status.updated_at}; "
                    f"{status.reason_zh}"
                )
                return 0
            if args.session_command == "clear":
                removed = clear_browser_session(config, args.provider_id)
                if removed:
                    removed_text = ", ".join(str(path) for path in removed)
                    print(f"已清除浏览器会话: provider={args.provider_id}; removed={removed_text}")
                else:
                    print(f"无需清除: provider={args.provider_id} 没有本地 browser session。")
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
    except (AssetError, AcquisitionError, BrowserSessionError) as exc:
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


def _run_visual_command(args: argparse.Namespace, root: Path) -> int:
    from .visual import (
        VisualError,
        extract_visual_evidence,
        parse_pages_spec,
        validate_visual_candidate_file,
        visual_status,
    )

    config = load_project_config(root)
    try:
        if args.visual_command == "extract":
            pages = parse_pages_spec(args.pages)
            result = extract_visual_evidence(
                config,
                args.paper_id,
                all_detected=args.all_detected,
                pages=pages,
                asset_suggestions_only=args.asset_suggestions_only,
            )
            print(
                "视觉证据候选提取完成: "
                f"{args.paper_id} -> 新增候选={result.candidates_created}, "
                f"裁图={result.crops_written}, 上下文包={result.context_packets_written}; "
                f"候选文件={result.candidate_path}"
            )
            return 0
        if args.visual_command == "validate":
            errors = validate_visual_candidate_file(config, args.paper_id)
            if errors:
                for error in errors:
                    print(f"视觉证据候选无效: {error}", file=sys.stderr)
                return 1
            print(f"视觉证据候选有效: {args.paper_id}")
            return 0
        if args.visual_command == "status":
            status = visual_status(config, args.paper_id)
            print(
                f"视觉证据候选状态: {args.paper_id} -> 总数={status.total_count}, "
                f"cropped={status.cropped_count}, ocr_success={status.ocr_success_count}, "
                f"ocr_partial={status.ocr_partial_count}, needs_review={status.needs_review_count}, "
                f"blocked={status.blocked_count}, not_run={status.not_run_count}; "
                f"候选文件={status.path}"
            )
            return 0
    except VisualError as exc:
        print(f"视觉证据操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_campaign_command(args: argparse.Namespace, root: Path) -> int:
    from .campaign import (
        CampaignError,
        campaign_status,
        create_campaign,
        generate_review_queue,
        import_campaign_items,
        pause_campaign_run,
        resume_campaign_run,
        review_campaign_queue_item,
        run_campaign,
        validate_campaign,
        validate_campaign_run,
        write_batch_report,
    )

    config = load_project_config(root)
    try:
        if args.campaign_command == "create":
            result = create_campaign(
                config,
                name_zh=args.name_zh,
                objective_zh=args.objective_zh,
                topic_profile=args.topic_profile,
                created_by=args.created_by,
            )
            print(f"已创建批量队列 {result.campaign_id}: {result.path}")
            return 0
        if args.campaign_command == "import":
            result = import_campaign_items(
                config,
                args.campaign_id,
                source_file=args.source_file,
                dedup=not args.no_dedup,
            )
            print(
                f"批量候选导入完成: {result.campaign_id} -> "
                f"导入={result.imported_count}, 重复={result.duplicate_count}, "
                f"已链接正式文献={result.linked_count}, 阻塞={result.blocked_count}; "
                f"文件={result.path}"
            )
            return 0
        if args.campaign_command == "validate":
            errors = validate_campaign(config, args.campaign_id)
            if errors:
                for error in errors:
                    print(f"批量队列无效: {error}", file=sys.stderr)
                return 1
            print(f"批量队列有效: {args.campaign_id}")
            return 0
        if args.campaign_command == "status":
            status = campaign_status(config, args.campaign_id)
            print(
                f"批量队列状态: {args.campaign_id} -> 总数={status.total_count}, "
                f"queued={status.queued_count}, linked={status.linked_count}, "
                f"duplicate={status.duplicate_count}, needs_review={status.needs_review_count}, "
                f"blocked={status.blocked_count}; 文件={status.path}"
            )
            return 0
        if args.campaign_command == "run":
            result = run_campaign(
                config,
                args.campaign_id,
                dry_run=args.dry_run,
                item_ids=args.item_ids,
                status_filter=args.status_filter,
                max_acquisition=args.max_acquisition,
                max_reading_draft=args.max_reading_draft,
                max_visual=args.max_visual,
                max_scoring=args.max_scoring,
            )
            errors = [] if args.dry_run else validate_campaign_run(config, args.campaign_id)
            if errors:
                for error in errors:
                    print(f"campaign run 校验失败: {error}", file=sys.stderr)
                return 1
            print(
                f"campaign 运行完成: {result.campaign_id} status={result.campaign_status}, "
                f"processed={result.processed_count}, linked={result.linked_count}, queued={result.queued_count}, "
                f"blocked={result.blocked_count}, formal_requests={result.formal_request_count}; "
                f"run={result.path}; queue={result.review_queue_path}; report={result.batch_report_path}"
            )
            return 0
        if args.campaign_command == "resume":
            result = resume_campaign_run(
                config,
                args.campaign_id,
                item_ids=args.item_ids,
                status_filter=args.status_filter,
            )
            print(
                f"campaign 恢复完成: {result.campaign_id} status={result.campaign_status}; "
                f"run={result.path}; queue={result.review_queue_path}; report={result.batch_report_path}"
            )
            return 0
        if args.campaign_command == "pause":
            result = pause_campaign_run(config, args.campaign_id, reason_zh=args.reason)
            print(
                f"campaign 已暂停: {result.campaign_id} status={result.campaign_status}; "
                f"run={result.path}; report={result.batch_report_path}"
            )
            return 0
        if args.campaign_command == "queue":
            if args.first == "review":
                if not args.second:
                    print("rsa campaign queue review 需要 campaign_id，例如 C001。", file=sys.stderr)
                    return 2
                if not args.queue_item_id or not args.decision or not args.reviewer:
                    print("queue review 需要 --item、--decision 和 --reviewer。", file=sys.stderr)
                    return 2
                result = review_campaign_queue_item(
                    config,
                    args.second,
                    queue_item_id=args.queue_item_id,
                    decision=args.decision,
                    reviewer=args.reviewer,
                    reason_zh=args.reason,
                )
                print(
                    f"review queue 已记录监管决策: {result.campaign_id} {result.item_id} "
                    f"decision={result.decision}; history={result.history_count}; 文件={result.path}"
                )
                return 0
            result = generate_review_queue(config, args.first)
            print(
                f"review queue 已生成: {result.campaign_id} -> total={result.total_count}, "
                f"blocked={result.blocked_count}, partial={result.partial_count}, "
                f"needs_review={result.needs_review_count}, auto_triaged={result.auto_triaged_count}, "
                f"high_priority={result.high_priority_count}, low_confidence={result.low_confidence_count}; "
                f"文件={result.path}"
            )
            return 0
        if args.campaign_command == "report":
            path = write_batch_report(config, args.campaign_id)
            print(f"campaign 批量报告已生成: {args.campaign_id} -> {path}")
            return 0
    except CampaignError as exc:
        print(f"批量队列操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_score_command(args: argparse.Namespace, root: Path) -> int:
    from .scoring import (
        ScoringError,
        review_score,
        score_campaign,
        score_paper,
        score_status,
        validate_scoring_record,
    )

    config = load_project_config(root)
    command = args.score_command
    target = args.score_target
    if not command:
        print(
            "评分命令缺少参数：请使用 rsa score P001，或 rsa score validate/status/review P001。",
            file=sys.stderr,
        )
        return 2

    try:
        if command == "validate":
            if not target:
                print("rsa score validate 需要 paper_id，例如 P001。", file=sys.stderr)
                return 2
            errors = validate_scoring_record(config, target)
            if errors:
                for error in errors:
                    print(f"评分记录无效: {error}", file=sys.stderr)
                return 1
            print(f"评分记录有效: {target}")
            return 0
        if command == "status":
            if not target:
                print("rsa score status 需要 paper_id，例如 P001。", file=sys.stderr)
                return 2
            status = score_status(config, target)
            if not status.exists:
                print(f"评分状态: {target} -> 未生成；文件={status.path}")
                return 0
            print(
                f"评分状态: {target} -> status={status.scoring_status}, "
                f"ai_review_decision={status.ai_review_decision}, "
                f"relevance={status.ai_relevance_score_10}/10, "
                f"quality={status.ai_quality_score_10}/10, "
                f"priority={status.ai_read_priority_score_10}/10, "
                f"confidence={status.score_confidence}, "
                f"human_final_decision={status.human_final_decision}; "
                f"文件={status.path}; review_packet={status.review_packet_path}"
            )
            return 0
        if command == "campaign":
            if not target:
                print("rsa score campaign 需要 campaign_id，例如 C001。", file=sys.stderr)
                return 2
            result = score_campaign(config, target)
            print(
                f"批量评分完成: {target} -> scored={result.scored_count}, "
                f"skipped={result.skipped_count}, blocked={result.blocked_count}, "
                f"needs_review={result.needs_review_count}, "
                f"recommend_pass={result.recommend_pass_count}, "
                f"recommend_defer={result.recommend_defer_count}; summary={result.path}"
            )
            return 0
        if command == "review":
            if not target:
                print("rsa score review 需要 paper_id，例如 P001。", file=sys.stderr)
                return 2
            result = review_score(
                config,
                target,
                final_decision=args.final_decision,
                reviewer=args.reviewer,
                reason=args.reason,
            )
            print(
                "评分人工监管已记录: "
                f"{target} -> final_decision={result.final_decision}, "
                f"history={result.history_count}; 文件={result.scoring_path}; "
                f"review_packet={result.review_packet_path}"
            )
            return 0

        result = score_paper(config, command, overwrite=args.overwrite)
        print(
            f"评分完成: {command} -> "
            f"relevance={result.ai_relevance_score_10}/10, "
            f"quality={result.ai_quality_score_10}/10, "
            f"priority={result.ai_read_priority_score_10}/10, "
            f"ai_review_decision={result.ai_review_decision}, "
            f"confidence={result.score_confidence}; "
            f"文件={result.scoring_path}; review_packet={result.review_packet_path}"
        )
        return 0
    except ScoringError as exc:
        print(f"评分操作失败: {exc}", file=sys.stderr)
        return 1


def _run_workflow_command(args: argparse.Namespace, root: Path) -> int:
    from .workflow import (
        STEP_IDS,
        WorkflowError,
        rerun_workflow,
        resume_workflow,
        run_workflow,
        stop_workflow,
        workflow_status,
    )

    config = load_project_config(root)
    paper_id = args.paper_id
    if paper_id.startswith("C"):
        print(
            "workflow 的主目标必须是单篇正式文献 P###；campaign 批量调度属于 Phase 11。",
            file=sys.stderr,
        )
        return 1
    try:
        if args.workflow_command == "run":
            skip_steps = _workflow_skip_steps(args)
            result = run_workflow(
                config,
                paper_id,
                campaign_id=args.campaign_id,
                campaign_item_id=args.campaign_item_id,
                skip_steps=skip_steps,
                from_step=args.from_step,
            )
            print(
                f"workflow 运行完成: {paper_id} run_id={result.run_id}, "
                f"status={result.workflow_status}, current_step={result.current_step}; "
                f"run={result.run_path}; report={result.report_path}; "
                f"next_action={_workflow_next_action_text(result.workflow_status)}"
            )
            return 0 if result.workflow_status in {"completed", "partial", "needs_review"} else 1
        if args.workflow_command == "resume":
            result = resume_workflow(config, paper_id, from_step=args.from_step)
            print(
                f"workflow 恢复完成: {paper_id} run_id={result.run_id}, "
                f"status={result.workflow_status}; report={result.report_path}; "
                f"next_action={_workflow_next_action_text(result.workflow_status)}"
            )
            return 0 if result.workflow_status in {"completed", "partial", "needs_review"} else 1
        if args.workflow_command == "status":
            status = workflow_status(config, paper_id)
            if not status.exists:
                print(f"workflow 状态: {paper_id} -> 尚未运行；目录={status.path}")
                return 0
            print(
                f"workflow 状态: {paper_id} run_id={status.run_id}, "
                f"status={status.workflow_status}, current_step={status.current_step}; "
                f"run={status.path}; report={status.report_path}; "
                f"next_action={_workflow_next_action_text(status.workflow_status)}"
            )
            return 0
        if args.workflow_command == "report":
            status = workflow_status(config, paper_id)
            if not status.exists or status.report_path is None or not status.report_path.exists():
                print(f"workflow report 不存在: {paper_id}", file=sys.stderr)
                return 1
            text = status.report_path.read_text(encoding="utf-8")
            first_lines = "\n".join(text.splitlines()[:12])
            print(f"workflow report: {status.report_path}\n{first_lines}")
            return 0
        if args.workflow_command == "stop":
            result = stop_workflow(config, paper_id, reason_zh=args.reason)
            print(
                f"workflow 已暂停: {paper_id} run_id={result.run_id}, "
                f"status={result.workflow_status}; report={result.report_path}; "
                f"next_action={_workflow_next_action_text(result.workflow_status)}"
            )
            return 0
        if args.workflow_command == "rerun":
            if args.from_step not in STEP_IDS:
                print(f"--from-step 必须是: {', '.join(STEP_IDS)}", file=sys.stderr)
                return 2
            result = rerun_workflow(config, paper_id, from_step=args.from_step)
            print(
                f"workflow 重新执行完成: {paper_id} run_id={result.run_id}, "
                f"from_step={args.from_step}, status={result.workflow_status}; "
                f"report={result.report_path}; "
                f"next_action={_workflow_next_action_text(result.workflow_status)}"
            )
            return 0 if result.workflow_status in {"completed", "partial", "needs_review"} else 1
    except WorkflowError as exc:
        print(f"workflow 操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _workflow_skip_steps(args: argparse.Namespace) -> list[str]:
    skip_steps: list[str] = []
    if getattr(args, "skip_acquisition", False):
        skip_steps.append("acquisition")
    if getattr(args, "skip_reading_draft", False):
        skip_steps.append("reading_draft")
    if getattr(args, "skip_visual", False):
        skip_steps.append("visual_extraction")
    if getattr(args, "skip_scoring", False):
        skip_steps.append("scoring")
    return skip_steps


def _workflow_next_action_text(status: str | None) -> str:
    if status == "completed":
        return "查看 review packet；如需正式写入，继续走 rsa formal 和人工确认。"
    if status == "needs_review":
        return "查看中文监管包，处理 needs_review 项。"
    if status == "partial":
        return "先查看 partial 原因，必要时用 workflow rerun 重跑对应步骤。"
    if status == "blocked":
        return "按修复提示补齐输入、授权或依赖后再 resume。"
    if status == "stopped":
        return "已暂停；后续必须显式指定 --from-step 才能恢复。"
    return "查看 workflow status 和 report。"


def _run_review_command(args: argparse.Namespace, root: Path) -> int:
    from .review_workspace import (
        ReviewWorkspaceError,
        build_review_workspace,
        clean_review_workspace,
        open_review_workspace,
        review_workspace_status,
    )

    config = load_project_config(root)
    try:
        if args.review_command == "build":
            result = build_review_workspace(
                config,
                campaign_id=args.campaign,
                paper_id=args.paper,
            )
            print(
                f"本地监管台已生成: target={result.target_type}:{result.target_id}, "
                f"objects={result.object_count}, actions={result.action_count}, "
                f"missing_links={result.missing_count}; index={result.index_path}; "
                f"manifest={result.manifest_path}"
            )
            return 0
        if args.review_command == "status":
            status = review_workspace_status(config)
            if not status.exists:
                print(f"本地监管台状态: 尚未生成；目录={status.root}")
                return 0
            print(
                f"本地监管台状态: target={status.target_type}:{status.target_id}, "
                f"objects={status.object_count}, actions={status.action_count}, "
                f"missing_links={status.missing_count}, generated_at={status.generated_at}; "
                f"index={status.index_path}; manifest={status.manifest_path}"
            )
            return 0
        if args.review_command == "open":
            path = open_review_workspace(config)
            print(f"已打开本地监管台: {path}")
            return 0
        if args.review_command == "clean":
            if not args.generated_only:
                print("review clean 需要 --generated-only，避免误删人工记录。", file=sys.stderr)
                return 2
            result = clean_review_workspace(config, generated_only=True)
            preserved = ", ".join(str(path) for path in result.preserved_paths) or "无"
            print(
                f"本地监管台生成文件已清理: removed={result.removed_count}; "
                f"preserved={preserved}; root={result.root}"
            )
            return 0
    except ReviewWorkspaceError as exc:
        print(f"本地监管台操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_safety_command(args: argparse.Namespace, root: Path) -> int:
    from .safety import (
        SafetyError,
        check_campaign_safety,
        check_paper_safety,
        safety_status,
        validate_campaign_safety_record,
        validate_safety_record,
    )

    config = load_project_config(root)
    try:
        if args.safety_command == "check":
            result = check_paper_safety(config, args.paper_id)
            print(
                f"写作安全检查完成: {args.paper_id} -> status={result.safety_status}, "
                f"claims={result.claim_count}, warnings={result.warning_count}, "
                f"blocked={result.blocked_count}; 文件={result.path}; report={result.report_path}"
            )
            return 0 if result.safety_status in {"passed", "needs_review"} else 1
        if args.safety_command == "validate":
            errors = validate_safety_record(config, args.paper_id)
            if errors:
                for error in errors:
                    print(f"safety 记录无效: {error}", file=sys.stderr)
                return 1
            print(f"safety 记录有效: {args.paper_id}")
            return 0
        if args.safety_command == "status":
            status = safety_status(config, args.paper_id)
            if not status.exists:
                print(f"safety 状态: {args.paper_id} -> missing; 文件={status.path}")
                return 0
            print(
                f"safety 状态: {args.paper_id} -> status={status.safety_status}, "
                f"claims={status.claim_count}, warnings={status.warning_count}, "
                f"blocked={status.blocked_count}, generated_at={status.generated_at}; "
                f"文件={status.path}; report={status.report_path}"
            )
            return 0
        if args.safety_command == "campaign":
            result = check_campaign_safety(config, args.campaign_id)
            errors = validate_campaign_safety_record(config, args.campaign_id)
            if errors:
                for error in errors:
                    print(f"campaign safety 记录无效: {error}", file=sys.stderr)
                return 1
            print(
                f"campaign 安全监测完成: {args.campaign_id} -> status={result.safety_status}, "
                f"checks={result.check_count}, warnings={result.warning_count}, "
                f"blocked={result.blocked_count}; 文件={result.path}; report={result.report_path}"
            )
            return 0 if result.safety_status in {"passed", "needs_review"} else 1
    except SafetyError as exc:
        print(f"safety 操作失败: {exc}", file=sys.stderr)
        return 1
    return 2


def _run_worker_command(args: argparse.Namespace, root: Path) -> int:
    from .worker import (
        WorkerError,
        add_worker_schedule,
        cancel_worker_task,
        enqueue_due_schedules,
        enqueue_worker_task,
        list_worker_schedules,
        read_worker_logs,
        recover_worker_task,
        run_worker,
        worker_status,
    )

    config = load_project_config(root)
    try:
        if args.worker_command == "enqueue":
            result = enqueue_worker_task(config, args.task_type, args.target_id)
            print(
                f"worker 任务已入队: {result.task_id} -> {result.task_type} "
                f"{result.target_id}; queue={result.path}; 正式写入仍需人工确认。"
            )
            return 0
        if args.worker_command == "run":
            result = run_worker(
                config,
                max_tasks=args.max_tasks,
                include_due=args.include_due,
            )
            print(
                f"worker 运行完成: processed={result.processed_count}, "
                f"completed={result.completed_count}, failed={result.failed_count}, "
                f"queued_remaining={result.queued_remaining_count}, "
                f"due_enqueued={result.due_enqueued_count}; queue={result.path}"
            )
            return 0 if result.failed_count == 0 else 1
        if args.worker_command == "status":
            status = worker_status(config)
            print(
                f"worker 状态: total={status.total_count}, queued={status.queued_count}, "
                f"running={status.running_count}, completed={status.completed_count}, "
                f"failed={status.failed_count}, cancelled={status.cancelled_count}, "
                f"schedules={status.enabled_schedule_count}/{status.schedule_count}, "
                f"last_task={status.last_task_id or '无'}; queue={status.path}; "
                f"schedules_file={status.schedule_path}; log={status.log_path}"
            )
            if status.last_message_zh:
                print(f"最近消息: {status.last_message_zh}")
            return 0
        if args.worker_command == "cancel":
            result = cancel_worker_task(config, args.task_id, reason_zh=args.reason)
            print(f"worker 任务已取消: {result.task_id}; queue={result.path}")
            return 0
        if args.worker_command == "recover":
            result = recover_worker_task(config, args.task_id, reason_zh=args.reason)
            print(f"worker 任务已恢复为 queued: {result.task_id}; queue={result.path}")
            return 0
        if args.worker_command == "logs":
            lines = read_worker_logs(config, max_lines=args.max_lines)
            if not lines:
                print("worker log 为空；尚未有入队或运行记录。")
                return 0
            print("\n".join(lines))
            return 0
        if args.worker_command == "schedule":
            if args.worker_schedule_command == "add":
                result = add_worker_schedule(
                    config,
                    args.task_type,
                    args.target_id,
                    interval_hours=args.interval_hours,
                    start_at=args.start_at,
                )
                print(
                    f"worker schedule 已新增: {result.schedule_id} -> {result.task_type} "
                    f"{result.target_id}; next_run_at={result.next_run_at}; "
                    f"schedules={result.path}"
                )
                return 0
            if args.worker_schedule_command == "list":
                schedules = list_worker_schedules(config)
                if not schedules:
                    print("worker schedule 为空。")
                    return 0
                for item in schedules:
                    print(
                        f"{item.get('schedule_id')} {item.get('task_type')} "
                        f"{item.get('target_id')} enabled={item.get('enabled')} "
                        f"next_run_at={item.get('next_run_at')}"
                    )
                return 0
            if args.worker_schedule_command == "due":
                result = enqueue_due_schedules(config)
                print(
                    f"到期 schedule 已入队: enqueued={result.enqueued_count}, "
                    f"schedules={','.join(result.due_schedule_ids) or '无'}; "
                    f"file={result.path}"
                )
                return 0
    except WorkerError as exc:
        print(f"worker 操作失败: {exc}", file=sys.stderr)
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
        if args.command == "visual":
            return _run_visual_command(args, root)
        if args.command == "campaign":
            return _run_campaign_command(args, root)
        if args.command == "score":
            return _run_score_command(args, root)
        if args.command == "workflow":
            return _run_workflow_command(args, root)
        if args.command == "review":
            return _run_review_command(args, root)
        if args.command == "safety":
            return _run_safety_command(args, root)
        if args.command == "worker":
            return _run_worker_command(args, root)
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
