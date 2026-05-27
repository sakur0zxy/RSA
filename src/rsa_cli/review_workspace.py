from __future__ import annotations

import html
import os
import shutil
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from .config import ProjectConfig
from .metadata import PAPER_ID_PATTERN


SCHEMA_VERSION = "phase12-review-workspace-v1"
MANIFEST_NAME = "review_workspace_manifest.yaml"
ACTION_CHECKLIST_NAME = "actions_checklist.md"
GENERATED_DIRECTORIES = {"groups", "objects"}
GENERATED_FILES = {"index.html", MANIFEST_NAME, ACTION_CHECKLIST_NAME}
USER_RECORDS_DIR = "user_records"

GROUP_ORDER = [
    "formal_write_request",
    "blocked",
    "partial",
    "needs_followup",
    "low_confidence",
    "high_priority",
    "auto_triaged",
    "completed_staging",
]
GROUP_LABELS_ZH = {
    "formal_write_request": "正式写入请求",
    "blocked": "阻塞项",
    "partial": "部分完成",
    "needs_followup": "需要补材料",
    "low_confidence": "低置信度",
    "high_priority": "高优先级",
    "auto_triaged": "机器已初审",
    "completed_staging": "已完成 staging",
}


class ReviewWorkspaceError(ValueError):
    """Raised when the local review workspace cannot be generated safely."""


@dataclass(frozen=True)
class ReviewWorkspaceBuildResult:
    target_type: str
    target_id: str
    root: Path
    index_path: Path
    manifest_path: Path
    action_checklist_path: Path
    object_count: int
    action_count: int
    missing_count: int


@dataclass(frozen=True)
class ReviewWorkspaceStatus:
    root: Path
    manifest_path: Path
    index_path: Path
    exists: bool
    target_type: str | None
    target_id: str | None
    generated_at: str | None
    object_count: int
    action_count: int
    missing_count: int


@dataclass(frozen=True)
class ReviewWorkspaceCleanResult:
    root: Path
    removed_count: int
    preserved_paths: list[Path]


def review_workspace_manifest_path(config: ProjectConfig) -> Path:
    return config.review_workspace_root / MANIFEST_NAME


def review_workspace_index_path(config: ProjectConfig) -> Path:
    return config.review_workspace_root / "index.html"


def build_review_workspace(
    config: ProjectConfig,
    *,
    campaign_id: str | None = None,
    paper_id: str | None = None,
) -> ReviewWorkspaceBuildResult:
    if bool(campaign_id) == bool(paper_id):
        raise ReviewWorkspaceError("必须且只能提供 --campaign 或 --paper 之一。")

    root = config.review_workspace_root
    root.mkdir(parents=True, exist_ok=True)
    (root / USER_RECORDS_DIR).mkdir(parents=True, exist_ok=True)
    _clean_generated(config)

    if campaign_id:
        target_type = "campaign"
        target_id = campaign_id
        objects = _collect_campaign_objects(config, campaign_id)
    else:
        target_type = "paper"
        target_id = str(paper_id)
        objects = _collect_paper_objects(config, target_id)

    _assign_object_ids(objects)
    actions = _build_actions(objects)
    pages = _render_workspace(config, target_type, target_id, objects, actions)
    manifest = _build_manifest(config, target_type, target_id, objects, actions, pages)
    manifest_path = review_workspace_manifest_path(config)
    _write_yaml(manifest_path, manifest)
    checklist_path = _write_actions_checklist(config, target_type, target_id, actions)
    return ReviewWorkspaceBuildResult(
        target_type=target_type,
        target_id=target_id,
        root=root,
        index_path=review_workspace_index_path(config),
        manifest_path=manifest_path,
        action_checklist_path=checklist_path,
        object_count=len(objects),
        action_count=len(actions),
        missing_count=sum(
            1
            for item in objects
            for link in item.get("artifact_links", [])
            if not link.get("exists")
        ),
    )


def review_workspace_status(config: ProjectConfig) -> ReviewWorkspaceStatus:
    root = config.review_workspace_root
    manifest_path = review_workspace_manifest_path(config)
    index_path = review_workspace_index_path(config)
    if not manifest_path.exists():
        return ReviewWorkspaceStatus(
            root=root,
            manifest_path=manifest_path,
            index_path=index_path,
            exists=False,
            target_type=None,
            target_id=None,
            generated_at=None,
            object_count=0,
            action_count=0,
            missing_count=0,
        )
    data = _read_yaml_mapping(manifest_path)
    objects = data.get("review_objects") if isinstance(data.get("review_objects"), list) else []
    actions = data.get("actions") if isinstance(data.get("actions"), list) else []
    return ReviewWorkspaceStatus(
        root=root,
        manifest_path=manifest_path,
        index_path=index_path,
        exists=True,
        target_type=_clean(data.get("target_type")),
        target_id=_clean(data.get("target_id")),
        generated_at=_clean(data.get("generated_at")),
        object_count=len(objects),
        action_count=len(actions),
        missing_count=int(data.get("missing_link_count") or 0),
    )


def open_review_workspace(config: ProjectConfig) -> Path:
    index_path = review_workspace_index_path(config)
    if not index_path.exists():
        raise ReviewWorkspaceError(
            f"review workspace 尚未生成；请先运行 rsa review build。缺失文件: {index_path}"
        )
    webbrowser.open(index_path.resolve().as_uri())
    return index_path


def clean_review_workspace(
    config: ProjectConfig, *, generated_only: bool = True
) -> ReviewWorkspaceCleanResult:
    if not generated_only:
        raise ReviewWorkspaceError("Phase 12 只支持 --generated-only，避免误删人工记录。")
    removed = _clean_generated(config)
    preserved = _preserved_paths(config)
    return ReviewWorkspaceCleanResult(
        root=config.review_workspace_root,
        removed_count=removed,
        preserved_paths=preserved,
    )


def _collect_campaign_objects(config: ProjectConfig, campaign_id: str) -> list[dict[str, Any]]:
    from .campaign import (
        campaign_batch_report_path,
        campaign_metadata_requests_path,
        campaign_path,
        campaign_review_queue_path,
        campaign_run_path,
        generate_review_queue,
    )

    try:
        queue_result = generate_review_queue(config, campaign_id)
    except Exception as exc:
        raise ReviewWorkspaceError(f"无法生成 campaign review queue: {exc}") from exc

    queue_data = _read_yaml_mapping(queue_result.path)
    queue_items = queue_data.get("queue_items") if isinstance(queue_data.get("queue_items"), list) else []
    common_links = [
        _artifact_link(config, "campaign", campaign_path(config, campaign_id), "campaign 主文件"),
        _artifact_link(config, "review_queue", campaign_review_queue_path(config, campaign_id), "监管队列"),
        _artifact_link(config, "run_ledger", campaign_run_path(config, campaign_id), "批量运行 ledger", "尚未运行 campaign run"),
        _artifact_link(config, "batch_report", campaign_batch_report_path(config, campaign_id), "中文批量报告", "需要运行 rsa campaign report"),
        _artifact_link(config, "metadata_requests", campaign_metadata_requests_path(config, campaign_id), "metadata intake 请求", "尚未生成 metadata intake request"),
    ]

    objects: list[dict[str, Any]] = []
    for item in queue_items:
        if not isinstance(item, dict):
            continue
        group = _group_for_campaign_item(item)
        title = _clean(item.get("title")) or _clean(item.get("queue_item_id")) or "未命名监管对象"
        links = list(common_links)
        links.extend(_artifact_link_from_mapping(config, link) for link in item.get("artifact_links", []) or [])
        objects.append(
            _review_object(
                title=title,
                object_type="campaign_queue_item",
                object_type_zh="campaign 监管队列项",
                group=group,
                status=_clean(item.get("status")) or "unknown",
                message_zh=_clean(item.get("message_zh"))
                or _clean(item.get("decision_meaning_zh"))
                or "该项需要用户在本地监管台查看。",
                risk_flags=list(item.get("risk_flags") or []),
                artifact_links=_unique_links(links),
                source={
                    "campaign_id": campaign_id,
                    "queue_item_id": item.get("queue_item_id"),
                    "source_type": item.get("source_type"),
                    "paper_id": item.get("paper_id"),
                    "source_campaign_item_id": item.get("source_campaign_item_id"),
                    "metadata_request_id": item.get("metadata_request_id"),
                    "formal_write_request_id": item.get("formal_write_request_id"),
                },
                ai={
                    "ai_review_decision": item.get("ai_review_decision"),
                    "ai_read_priority_score_10": item.get("ai_read_priority_score_10"),
                    "score_confidence": item.get("score_confidence"),
                    "triage_confidence": item.get("triage_confidence"),
                    "recommended_action": item.get("recommended_action"),
                },
                formal_gate_required=_is_formal_related(item),
            )
        )
    if not objects:
        objects.append(
            _review_object(
                title=f"{campaign_id} 暂无待监管项",
                object_type="campaign_overview",
                object_type_zh="campaign 总览",
                group="completed_staging",
                status="empty",
                message_zh="当前 campaign review queue 没有待处理对象；可查看 campaign 文件或重新运行 campaign run。",
                risk_flags=[],
                artifact_links=common_links,
                source={"campaign_id": campaign_id},
                ai={},
                formal_gate_required=False,
            )
        )
    return objects


def _collect_paper_objects(config: ProjectConfig, paper_id: str) -> list[dict[str, Any]]:
    if not PAPER_ID_PATTERN.match(paper_id):
        raise ReviewWorkspaceError(f"paper_id 必须匹配 P###: {paper_id}")

    from .assets import asset_manifest_path, source_record_path
    from .notes import note_path
    from .scoring import review_packet_path as scoring_review_packet_path
    from .scoring import score_status, scoring_path
    from .visual import visual_candidate_path, visual_status
    from .workflow import workflow_status

    metadata_path = config.metadata_root / f"{paper_id}.yaml"
    source_path = source_record_path(config, paper_id)
    note_file = note_path(config, paper_id)
    note_packet = config.notes_root / f"{paper_id}_review_packet.md"
    asset_manifest = asset_manifest_path(config, paper_id)
    visual_file = visual_candidate_path(config, paper_id)
    scoring_file = scoring_path(config, paper_id)
    scoring_packet = scoring_review_packet_path(config, paper_id)
    workflow = workflow_status(config, paper_id)
    visual = visual_status(config, paper_id)
    score = score_status(config, paper_id)
    note_data = _read_note_frontmatter(note_file) if note_file.exists() else {}

    common = [
        _artifact_link(config, "metadata", metadata_path, "正式 metadata", "需要先通过 rsa add-paper 写入正式 metadata"),
        _artifact_link(config, "source_ledger", source_path, "来源 ledger", "需要补充授权全文来源"),
        _artifact_link(config, "asset_manifest", asset_manifest, "资产 manifest", "尚未登记截图或图表资产"),
    ]

    objects = [
        _review_object(
            title=f"{paper_id} 文献总览",
            object_type="paper_overview",
            object_type_zh="单篇论文总览",
            group="completed_staging" if metadata_path.exists() else "blocked",
            status="metadata_available" if metadata_path.exists() else "metadata_missing",
            message_zh=(
                "正式 metadata 已存在；监管台会聚合阅读、视觉、评分和 workflow 证据。"
                if metadata_path.exists()
                else "缺少正式 metadata，无法形成完整单篇监管链。"
            ),
            risk_flags=[] if metadata_path.exists() else ["missing_metadata"],
            artifact_links=common,
            source={"paper_id": paper_id},
            ai={},
            formal_gate_required=False,
        ),
        _review_object(
            title=f"{paper_id} reading note",
            object_type="reading_note",
            object_type_zh="阅读草稿监管",
            group=_group_for_note(note_file.exists(), note_data),
            status=_clean(note_data.get("note_status")) or ("missing" if not note_file.exists() else "unknown"),
            message_zh=_note_message(note_file.exists(), note_data),
            risk_flags=[] if note_file.exists() else ["missing_reading_note"],
            artifact_links=[
                _artifact_link(config, "reading_note", note_file, "阅读笔记", "需要运行 rsa note draft 或 rsa note create"),
                _artifact_link(config, "reading_review_packet", note_packet, "阅读监管包", "需要重新生成 reading draft"),
                *common,
            ],
            source={"paper_id": paper_id},
            ai={"agent_review_score_10": note_data.get("agent_review_score_10")},
            formal_gate_required=bool(note_data.get("note_integration_requests")),
        ),
        _review_object(
            title=f"{paper_id} workflow",
            object_type="workflow_run",
            object_type_zh="单篇自动工作流",
            group=_group_for_status(workflow.workflow_status),
            status=workflow.workflow_status or "not_run",
            message_zh=_workflow_message(workflow.workflow_status, workflow.current_step),
            risk_flags=_risk_for_status(workflow.workflow_status),
            artifact_links=[
                _artifact_link(config, "workflow_run", workflow.path, "workflow run YAML", "尚未运行 rsa workflow run"),
                _artifact_link(config, "workflow_report", workflow.report_path, "workflow 中文监管包", "需要运行 rsa workflow report 或重新运行 workflow"),
                *common,
            ],
            source={"paper_id": paper_id, "current_step": workflow.current_step},
            ai={},
            formal_gate_required=False,
        ),
        _review_object(
            title=f"{paper_id} visual evidence",
            object_type="visual_evidence",
            object_type_zh="视觉证据候选监管",
            group=_group_for_visual(visual.total_count, visual.needs_review_count, visual.blocked_count),
            status="generated" if visual.total_count else "missing",
            message_zh=_visual_message(visual.total_count, visual.needs_review_count, visual.blocked_count),
            risk_flags=_visual_risks(visual.total_count, visual.needs_review_count, visual.blocked_count),
            artifact_links=[
                _artifact_link(config, "visual_candidates", visual_file, "视觉证据候选", "需要运行 rsa visual extract"),
                _artifact_link(config, "asset_manifest", asset_manifest, "资产 manifest", "尚未登记资产 manifest"),
                *common,
            ],
            source={"paper_id": paper_id},
            ai={"candidate_count": visual.total_count},
            formal_gate_required=False,
        ),
        _review_object(
            title=f"{paper_id} AI scoring",
            object_type="ai_scoring",
            object_type_zh="AI 辅助评分监管",
            group=_group_for_score(score),
            status=score.scoring_status or "missing",
            message_zh=_score_message(score),
            risk_flags=_score_risks(score),
            artifact_links=[
                _artifact_link(config, "scoring_yaml", scoring_file, "scoring YAML", "需要运行 rsa score P###"),
                _artifact_link(config, "scoring_review_packet", scoring_packet, "评分监管包", "需要运行 rsa score P###"),
                *common,
            ],
            source={"paper_id": paper_id},
            ai={
                "ai_review_decision": score.ai_review_decision,
                "ai_relevance_score_10": score.ai_relevance_score_10,
                "ai_quality_score_10": score.ai_quality_score_10,
                "ai_read_priority_score_10": score.ai_read_priority_score_10,
                "score_confidence": score.score_confidence,
                "human_final_decision": score.human_final_decision,
            },
            formal_gate_required=False,
        ),
    ]
    return objects


def _review_object(
    *,
    title: str,
    object_type: str,
    object_type_zh: str,
    group: str,
    status: str,
    message_zh: str,
    risk_flags: list[str],
    artifact_links: list[dict[str, Any]],
    source: dict[str, Any],
    ai: dict[str, Any],
    formal_gate_required: bool,
) -> dict[str, Any]:
    group = group if group in GROUP_ORDER else "completed_staging"
    return {
        "review_object_id": None,
        "title": title,
        "object_type": object_type,
        "object_type_zh": object_type_zh,
        "group": group,
        "group_zh": GROUP_LABELS_ZH[group],
        "status": status,
        "message_zh": message_zh,
        "risk_flags": risk_flags,
        "artifact_links": artifact_links,
        "source": source,
        "ai": {key: value for key, value in ai.items() if value is not None},
        "formal_gate_required": formal_gate_required,
        "formal_gate_policy_zh": (
            "该对象涉及正式写入时，必须继续通过 rsa formal 或 add-paper 的人工确认门禁。"
            if formal_gate_required
            else "该对象属于 staging/review 监管，不会直接写入正式记录。"
        ),
        "suggested_actions": [],
    }


def _assign_object_ids(objects: list[dict[str, Any]]) -> None:
    objects.sort(key=lambda item: (_group_index(str(item.get("group"))), str(item.get("title") or "")))
    for index, item in enumerate(objects, start=1):
        item["review_object_id"] = f"RO{index:03d}"


def _build_actions(objects: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for item in objects:
        object_actions = _actions_for_object(item)
        for action in object_actions:
            action["action_id"] = f"RA{len(actions) + 1:03d}"
            action["review_object_id"] = item.get("review_object_id")
            actions.append(action)
        item["suggested_actions"] = object_actions
    return actions


def _actions_for_object(item: dict[str, Any]) -> list[dict[str, Any]]:
    source = item.get("source") if isinstance(item.get("source"), dict) else {}
    paper_id = source.get("paper_id")
    campaign_id = source.get("campaign_id")
    queue_item_id = source.get("queue_item_id")
    object_type = item.get("object_type")
    actions: list[dict[str, Any]] = []

    if object_type == "campaign_queue_item" and campaign_id and queue_item_id:
        formal = bool(item.get("formal_gate_required"))
        actions.append(
            _action(
                label_zh="记录监管队列处理意见",
                reason_zh="该命令只记录 review decision，不等于正式批准。",
                command=(
                    f"rsa campaign queue review {campaign_id} --item {queue_item_id} "
                    '--decision accepted --reviewer zxy --reason "人工监管后接受进入后续流程。"'
                ),
                formal_gate_required=formal,
            )
        )
    if object_type == "reading_note" and paper_id:
        if item.get("status") == "missing":
            actions.append(
                _action(
                    label_zh="生成阅读草稿",
                    reason_zh="缺少 reading note，需先补齐授权全文或来源 ledger。",
                    command=f"rsa note draft {paper_id}",
                    formal_gate_required=False,
                )
            )
        else:
            actions.append(
                _action(
                    label_zh="校验阅读笔记",
                    reason_zh="确认 reading note schema 与人工监管字段有效。",
                    command=f"rsa note validate {paper_id}",
                    formal_gate_required=False,
                )
            )
            if item.get("formal_gate_required"):
                actions.append(
                    _action(
                        label_zh="人工确认后应用 note 派生正式写入",
                        reason_zh="该命令会触发 formal write gate，必须显式人工确认。",
                        command=f"rsa formal apply-note --source-note {paper_id} --human-confirmed --confirmed-by zxy",
                        formal_gate_required=True,
                    )
                )
    if object_type == "workflow_run" and paper_id:
        current_step = source.get("current_step")
        if item.get("status") in {"blocked", "failed", "partial"}:
            command = f"rsa workflow resume {paper_id}"
            if current_step:
                command += f" --from-step {current_step}"
            actions.append(
                _action(
                    label_zh="修复输入后恢复 workflow",
                    reason_zh="workflow 已阻塞或部分完成，需先按报告修复再恢复。",
                    command=command,
                    formal_gate_required=False,
                )
            )
        actions.append(
            _action(
                label_zh="查看 workflow 状态",
                reason_zh="只读查看当前步骤、状态和中文监管包路径。",
                command=f"rsa workflow status {paper_id}",
                formal_gate_required=False,
            )
        )
    if object_type == "visual_evidence" and paper_id:
        actions.append(
            _action(
                label_zh="生成或刷新视觉证据候选",
                reason_zh="视觉候选只进入 staging/review，用于人工查看图表证据。",
                command=f"rsa visual extract {paper_id}",
                formal_gate_required=False,
            )
        )
    if object_type == "ai_scoring" and paper_id:
        actions.append(
            _action(
                label_zh="记录评分人工监管",
                reason_zh="人工监管评分只影响 scoring review history，不是 formal approval。",
                command=(
                    f"rsa score review {paper_id} --final-decision approved "
                    '--reviewer zxy --reason "人工复核后认为该评分可作为排序参考。"'
                ),
                formal_gate_required=False,
            )
        )
    if not actions and paper_id:
        actions.append(
            _action(
                label_zh="查看单篇 workflow 状态",
                reason_zh="从单篇自动链路入口确认当前状态。",
                command=f"rsa workflow status {paper_id}",
                formal_gate_required=False,
            )
        )
    return actions


def _action(
    *,
    label_zh: str,
    reason_zh: str,
    command: str,
    formal_gate_required: bool,
) -> dict[str, Any]:
    return {
        "action_id": None,
        "label_zh": label_zh,
        "reason_zh": reason_zh,
        "command": command,
        "formal_gate_required": formal_gate_required,
        "execution_policy_zh": "本地监管台只展示命令，不自动执行，也不直接修改文件。",
    }


def _build_manifest(
    config: ProjectConfig,
    target_type: str,
    target_id: str,
    objects: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    pages: dict[str, Any],
) -> dict[str, Any]:
    missing_links = [
        {
            "review_object_id": item.get("review_object_id"),
            "label": link.get("label"),
            "path": link.get("path"),
            "missing_zh": link.get("missing_zh"),
        }
        for item in objects
        for link in item.get("artifact_links", [])
        if not link.get("exists")
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": _now(),
        "user_language": "zh",
        "target_type": target_type,
        "target_id": target_id,
        "workspace_root": _display_path(config, config.review_workspace_root),
        "pages": pages,
        "group_order": GROUP_ORDER,
        "groups": [
            {
                "group": group,
                "label_zh": GROUP_LABELS_ZH[group],
                "count": sum(1 for item in objects if item.get("group") == group),
                "page": _display_path(config, config.review_workspace_root / "groups" / f"{group}.html"),
            }
            for group in GROUP_ORDER
            if any(item.get("group") == group for item in objects)
        ],
        "review_objects": objects,
        "actions": actions,
        "missing_links": missing_links,
        "missing_link_count": len(missing_links),
        "formal_gate_policy_zh": (
            "review workspace 是本地监管入口，不是正式写入入口；metadata、literature_map、"
            "agent_research_notes 等正式记录仍必须通过人工确认命令。"
        ),
        "rebuild_policy_zh": (
            "重复运行 build 会覆盖生成的 HTML/manifest/checklist，保留 user_records 等人工记录。"
        ),
    }


def _render_workspace(
    config: ProjectConfig,
    target_type: str,
    target_id: str,
    objects: list[dict[str, Any]],
    actions: list[dict[str, Any]],
) -> dict[str, Any]:
    root = config.review_workspace_root
    groups_dir = root / "groups"
    objects_dir = root / "objects"
    groups_dir.mkdir(parents=True, exist_ok=True)
    objects_dir.mkdir(parents=True, exist_ok=True)

    for item in objects:
        page = objects_dir / f"{item['review_object_id']}.html"
        page.write_text(_render_object_page(config, item, page), encoding="utf-8")
        item["page"] = _display_path(config, page)

    group_pages = {}
    for group in GROUP_ORDER:
        group_objects = [item for item in objects if item.get("group") == group]
        if not group_objects:
            continue
        page = groups_dir / f"{group}.html"
        page.write_text(
            _render_group_page(config, group, group_objects, page),
            encoding="utf-8",
        )
        group_pages[group] = _display_path(config, page)

    index_path = review_workspace_index_path(config)
    index_path.write_text(
        _render_index_page(config, target_type, target_id, objects, actions, index_path),
        encoding="utf-8",
    )
    return {
        "index": _display_path(config, index_path),
        "groups": group_pages,
        "objects": {item["review_object_id"]: item["page"] for item in objects},
        "actions_checklist": _display_path(config, config.review_workspace_root / ACTION_CHECKLIST_NAME),
        "manifest": _display_path(config, review_workspace_manifest_path(config)),
    }


def _render_index_page(
    config: ProjectConfig,
    target_type: str,
    target_id: str,
    objects: list[dict[str, Any]],
    actions: list[dict[str, Any]],
    page_path: Path,
) -> str:
    stats = "".join(
        f"<li><a href='{_href(config, config.review_workspace_root / 'groups' / (group + '.html'), page_path)}'>{_e(GROUP_LABELS_ZH[group])}</a>: {count}</li>"
        for group, count in _group_counts(objects).items()
    )
    urgent = "".join(_object_card(config, item, page_path) for item in objects[:12])
    action_html = "".join(_action_card(action) for action in actions[:12]) or "<p>暂无建议动作。</p>"
    body = f"""
<section>
  <h2>总览</h2>
  <p>目标：<code>{_e(target_type)}</code> / <code>{_e(target_id)}</code></p>
  <p>本地监管台只负责查看、导航和展示 CLI 命令；不会直接修改文件，也不会绕过 formal write gate。</p>
  <ul>{stats}</ul>
</section>
<section>
  <h2>优先处理</h2>
  <div class="grid">{urgent}</div>
</section>
<section>
  <h2>建议动作</h2>
  <p><a href="{_href(config, config.review_workspace_root / ACTION_CHECKLIST_NAME, page_path)}">打开 Markdown 操作清单</a></p>
  <div class="actions">{action_html}</div>
</section>
"""
    return _page_shell(f"RSA 本地监管台 - {target_id}", body)


def _render_group_page(
    config: ProjectConfig, group: str, objects: list[dict[str, Any]], page_path: Path
) -> str:
    cards = "".join(_object_card(config, item, page_path) for item in objects)
    body = f"""
<p><a href="{_href(config, review_workspace_index_path(config), page_path)}">返回首页</a></p>
<h2>{_e(GROUP_LABELS_ZH[group])}</h2>
<div class="grid">{cards}</div>
"""
    return _page_shell(f"{GROUP_LABELS_ZH[group]} - RSA 本地监管台", body)


def _render_object_page(config: ProjectConfig, item: dict[str, Any], page_path: Path) -> str:
    links = "".join(_artifact_link_html(config, link, page_path) for link in item.get("artifact_links", []))
    ai = item.get("ai") if isinstance(item.get("ai"), dict) else {}
    ai_items = "".join(f"<li><code>{_e(key)}</code>: {_e(value)}</li>" for key, value in ai.items())
    actions = "".join(_action_card(action) for action in item.get("suggested_actions", [])) or "<p>暂无建议动作。</p>"
    risks = ", ".join(str(flag) for flag in item.get("risk_flags", []) or []) or "无"
    body = f"""
<p><a href="{_href(config, review_workspace_index_path(config), page_path)}">返回首页</a></p>
<section>
  <h2>{_e(item.get("title"))}</h2>
  <p>类型：{_e(item.get("object_type_zh"))} / <code>{_e(item.get("object_type"))}</code></p>
  <p>分组：{_e(item.get("group_zh"))} / <code>{_e(item.get("group"))}</code></p>
  <p>状态：<code>{_e(item.get("status"))}</code></p>
  <p>{_e(item.get("message_zh"))}</p>
  <p>风险标记：<code>{_e(risks)}</code></p>
  <p>{_e(item.get("formal_gate_policy_zh"))}</p>
</section>
<section>
  <h2>证据链接</h2>
  <ul>{links}</ul>
</section>
<section>
  <h2>AI/自动化信息</h2>
  <ul>{ai_items or "<li>无额外 AI 信息。</li>"}</ul>
</section>
<section>
  <h2>建议动作</h2>
  <div class="actions">{actions}</div>
</section>
"""
    return _page_shell(f"{item.get('review_object_id')} - RSA 本地监管台", body)


def _page_shell(title: str, body: str) -> str:
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <style>
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; color: #172026; background: #f6f8fa; }}
    header {{ background: #12343b; color: white; padding: 20px 28px; }}
    main {{ max-width: 1120px; margin: 0 auto; padding: 24px; }}
    section {{ margin: 0 0 24px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 12px; }}
    .card, .action {{ background: white; border: 1px solid #d7dee5; border-radius: 8px; padding: 14px; }}
    .meta {{ color: #596773; font-size: 0.92rem; }}
    code {{ background: #eef2f5; padding: 2px 4px; border-radius: 4px; }}
    pre {{ white-space: pre-wrap; word-break: break-word; background: #101820; color: #f5f7fa; padding: 10px; border-radius: 6px; }}
    a {{ color: #0b63ce; }}
    .missing {{ color: #a53b00; font-weight: 600; }}
  </style>
</head>
<body>
  <header>
    <h1>{_e(title)}</h1>
    <p>中文本地监管包。用于查看 staging/review 证据与建议命令，不执行正式写入。</p>
  </header>
  <main>
    {body}
  </main>
</body>
</html>
"""


def _object_card(config: ProjectConfig, item: dict[str, Any], page_path: Path) -> str:
    object_page = config.root / str(item.get("page"))
    return f"""
<article class="card">
  <h3><a href="{_href(config, object_page, page_path)}">{_e(item.get("title"))}</a></h3>
  <p class="meta">{_e(item.get("object_type_zh"))} · <code>{_e(item.get("status"))}</code></p>
  <p>{_e(item.get("message_zh"))}</p>
  <p class="meta">formal gate: <code>{str(bool(item.get("formal_gate_required"))).lower()}</code></p>
</article>
"""


def _action_card(action: dict[str, Any]) -> str:
    return f"""
<article class="action">
  <h3>{_e(action.get("label_zh"))}</h3>
  <p>{_e(action.get("reason_zh"))}</p>
  <p>formal gate: <code>{str(bool(action.get("formal_gate_required"))).lower()}</code></p>
  <pre>{_e(action.get("command"))}</pre>
</article>
"""


def _artifact_link_html(config: ProjectConfig, link: dict[str, Any], page_path: Path) -> str:
    label = f"{link.get('label_zh') or link.get('label')} / {link.get('label')}"
    if link.get("exists"):
        target = _path_from_link(config, link)
        href = _href(config, target, page_path)
        return f"<li><a href=\"{href}\">{_e(label)}</a> <code>{_e(link.get('path'))}</code></li>"
    return (
        f"<li><span class='missing'>{_e(label)}：{_e(link.get('missing_zh'))}</span> "
        f"<code>{_e(link.get('path'))}</code></li>"
    )


def _write_actions_checklist(
    config: ProjectConfig,
    target_type: str,
    target_id: str,
    actions: list[dict[str, Any]],
) -> Path:
    path = config.review_workspace_root / ACTION_CHECKLIST_NAME
    lines = [
        f"# RSA 本地监管台操作清单: {target_type} {target_id}",
        "",
        "本清单只展示建议命令，不会自动执行。涉及正式记录写入时仍必须通过人工确认门禁。",
        "",
    ]
    if not actions:
        lines.append("暂无建议动作。")
    for action in actions:
        lines.extend(
            [
                f"## {action.get('action_id')} - {action.get('label_zh')}",
                "",
                f"- review_object_id: `{action.get('review_object_id')}`",
                f"- formal_gate_required: `{str(bool(action.get('formal_gate_required'))).lower()}`",
                f"- 中文原因: {action.get('reason_zh')}",
                "",
                "```powershell",
                str(action.get("command") or ""),
                "```",
                "",
            ]
        )
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _artifact_link(
    config: ProjectConfig,
    label: str,
    path: str | Path | None,
    label_zh: str,
    missing_zh: str | None = None,
) -> dict[str, Any]:
    if path is None:
        return {
            "label": label,
            "label_zh": label_zh,
            "path": None,
            "exists": False,
            "missing_zh": missing_zh or "文件缺失，需要重新生成或补充。",
        }
    resolved = _resolve_path(config, path)
    exists = resolved.exists()
    return {
        "label": label,
        "label_zh": label_zh,
        "path": _display_path(config, resolved),
        "exists": exists,
        "missing_zh": None if exists else (missing_zh or "文件缺失，需要重新生成或补充。"),
    }


def _artifact_link_from_mapping(config: ProjectConfig, value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return _artifact_link(
            config,
            str(value.get("label") or "artifact"),
            value.get("path"),
            _artifact_label_zh(str(value.get("label") or "artifact")),
        )
    return _artifact_link(config, "artifact", value, "证据文件")


def _artifact_label_zh(label: str) -> str:
    mapping = {
        "campaign": "campaign 主文件",
        "run_ledger": "运行 ledger",
        "workflow_report": "workflow 监管包",
        "scoring_record": "scoring YAML",
        "review_packet": "监管包",
        "metadata_requests": "metadata 请求",
        "batch_report": "批量报告",
    }
    return mapping.get(label, label)


def _group_for_campaign_item(item: dict[str, Any]) -> str:
    if _is_formal_related(item):
        return "formal_write_request"
    decision = item.get("review_decision")
    if decision == "needs_followup":
        return "needs_followup"
    group = str(item.get("queue_group") or "")
    risk_flags = set(item.get("risk_flags") or [])
    if group in {"blocked", "partial", "auto_triaged", "completed_staging"}:
        return group
    if group == "needs_review":
        return "needs_followup"
    if "low_confidence" in risk_flags:
        return "low_confidence"
    if "high_priority" in risk_flags:
        return "high_priority"
    return "completed_staging"


def _is_formal_related(item: dict[str, Any]) -> bool:
    source_type = str(item.get("source_type") or "")
    risks = set(item.get("risk_flags") or [])
    return source_type == "formal_write_request" or "formal_write_pending" in risks


def _group_for_note(exists: bool, data: dict[str, Any]) -> str:
    if not exists:
        return "blocked"
    status = str(data.get("note_status") or "")
    if status == "blocked":
        return "blocked"
    if status in {"draft", "ready_for_review"}:
        return "needs_followup"
    return "completed_staging"


def _group_for_status(status: str | None) -> str:
    if status in {"blocked", "failed"}:
        return "blocked"
    if status == "partial":
        return "partial"
    if status in {"needs_review", "stopped"}:
        return "needs_followup"
    if status in {"completed"}:
        return "completed_staging"
    return "auto_triaged"


def _group_for_visual(total: int, needs_review: int, blocked: int) -> str:
    if blocked:
        return "blocked"
    if needs_review:
        return "needs_followup"
    if total:
        return "completed_staging"
    return "partial"


def _group_for_score(score: Any) -> str:
    if not getattr(score, "exists", False):
        return "partial"
    if getattr(score, "ai_review_decision", None) == "needs_review":
        return "needs_followup"
    if getattr(score, "score_confidence", None) == "low":
        return "low_confidence"
    priority = getattr(score, "ai_read_priority_score_10", None)
    if isinstance(priority, int) and priority >= 8:
        return "high_priority"
    return "completed_staging"


def _note_message(exists: bool, data: dict[str, Any]) -> str:
    if not exists:
        return "缺少 reading note；请先补充授权全文并运行 rsa note draft 或 rsa note create。"
    status = data.get("note_status") or "unknown"
    return f"reading note 已存在，note_status={status}。请检查 source_grounded_claims、short_quotes、agent_summary 和 human_decision。"


def _workflow_message(status: str | None, current_step: str | None) -> str:
    if not status:
        return "尚未运行单篇 workflow；可运行 rsa workflow run P###。"
    if status == "completed":
        return "workflow 已完成 staging/review packet；正式写入仍需人工确认。"
    if status == "partial":
        return "workflow 部分完成；请查看 report 中的 partial_reason_zh。"
    if status in {"blocked", "failed"}:
        return f"workflow 已阻塞在 {current_step or 'unknown'}；请按 repair_hint_zh 修复后再 resume。"
    if status == "needs_review":
        return "workflow 已进入需要人工监管的状态。"
    if status == "stopped":
        return "workflow 被用户暂停；恢复时必须显式指定位置。"
    return f"workflow 当前状态为 {status}。"


def _visual_message(total: int, needs_review: int, blocked: int) -> str:
    if blocked:
        return f"存在 {blocked} 个 blocked 视觉候选，需要人工查看 PDF/截图和候选记录。"
    if needs_review:
        return f"存在 {needs_review} 个需要复核的视觉候选。"
    if total:
        return f"已生成 {total} 个视觉证据候选；这些只是 staging/review 材料。"
    return "尚未生成视觉证据候选；需要图表证据时运行 rsa visual extract。"


def _score_message(score: Any) -> str:
    if not getattr(score, "exists", False):
        return "尚未生成 AI 辅助评分；可运行 rsa score P###。"
    return (
        f"评分已生成：relevance={score.ai_relevance_score_10}/10, "
        f"quality={score.ai_quality_score_10}/10, priority={score.ai_read_priority_score_10}/10, "
        f"confidence={score.score_confidence}。评分只用于排序和监管，不是 formal approval。"
    )


def _risk_for_status(status: str | None) -> list[str]:
    if status in {"blocked", "failed"}:
        return ["blocked"]
    if status == "partial":
        return ["partial"]
    if status == "needs_review":
        return ["needs_review"]
    if status == "stopped":
        return ["stopped_by_user"]
    return []


def _visual_risks(total: int, needs_review: int, blocked: int) -> list[str]:
    risks = []
    if not total:
        risks.append("missing_visual_evidence")
    if needs_review:
        risks.append("visual_needs_review")
    if blocked:
        risks.append("visual_blocked")
    return risks


def _score_risks(score: Any) -> list[str]:
    if not getattr(score, "exists", False):
        return ["missing_scoring"]
    risks = []
    if getattr(score, "score_confidence", None) == "low":
        risks.append("low_confidence")
    priority = getattr(score, "ai_read_priority_score_10", None)
    if isinstance(priority, int) and priority >= 8:
        risks.append("high_priority")
    if getattr(score, "ai_review_decision", None) == "needs_review":
        risks.append("needs_review")
    return risks


def _group_counts(objects: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for group in GROUP_ORDER:
        count = sum(1 for item in objects if item.get("group") == group)
        if count:
            counts[group] = count
    return counts


def _group_index(group: str) -> int:
    try:
        return GROUP_ORDER.index(group)
    except ValueError:
        return len(GROUP_ORDER)


def _clean_generated(config: ProjectConfig) -> int:
    root = config.review_workspace_root
    root.mkdir(parents=True, exist_ok=True)
    removed = 0
    for name in GENERATED_FILES:
        path = root / name
        if path.exists():
            path.unlink()
            removed += 1
    for name in GENERATED_DIRECTORIES:
        path = root / name
        if path.exists():
            _ensure_under_root(root, path)
            shutil.rmtree(path)
            removed += 1
    return removed


def _preserved_paths(config: ProjectConfig) -> list[Path]:
    root = config.review_workspace_root
    preserved = []
    for child in [root / USER_RECORDS_DIR, root / ".gitkeep"]:
        if child.exists():
            preserved.append(child)
    return preserved


def _ensure_under_root(root: Path, path: Path) -> None:
    root_resolved = root.resolve()
    path_resolved = path.resolve()
    if root_resolved not in [path_resolved, *path_resolved.parents]:
        raise ReviewWorkspaceError(f"拒绝清理 review workspace 外的路径: {path}")


def _read_note_frontmatter(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    loaded = yaml.safe_load(parts[1]) or {}
    return loaded if isinstance(loaded, dict) else {}


def _read_yaml_mapping(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except OSError as exc:
        raise ReviewWorkspaceError(f"无法读取 YAML: {path}: {exc}") from exc
    except yaml.YAMLError as exc:
        raise ReviewWorkspaceError(f"YAML 无效: {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ReviewWorkspaceError(f"YAML 必须是 mapping: {path}")
    return loaded


def _write_yaml(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _unique_links(links: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    seen = set()
    for link in links:
        key = (link.get("label"), link.get("path"))
        if key in seen:
            continue
        seen.add(key)
        out.append(link)
    return out


def _path_from_link(config: ProjectConfig, link: dict[str, Any]) -> Path:
    value = link.get("path")
    if not value:
        return config.review_workspace_root
    return _resolve_path(config, value)


def _resolve_path(config: ProjectConfig, value: str | Path) -> Path:
    path = Path(value)
    if path.is_absolute():
        return path
    return config.root / path


def _display_path(config: ProjectConfig, path: Path) -> str:
    try:
        return path.resolve().relative_to(config.root).as_posix()
    except ValueError:
        return str(path)


def _href(config: ProjectConfig, target: Path, page_path: Path) -> str:
    if not target.is_absolute():
        target = config.root / target
    try:
        rel = os.path.relpath(target.resolve(), page_path.parent.resolve())
    except OSError:
        rel = str(target)
    return html.escape(Path(rel).as_posix(), quote=True)


def _e(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def _clean(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
