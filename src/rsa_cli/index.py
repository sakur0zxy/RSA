from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import ProjectConfig
from .metadata import load_metadata_record, validate_metadata_record


class IndexError(ValueError):
    """Raised when paper index generation cannot safely proceed."""


def _paper_sort_key(record: dict[str, Any]) -> int:
    paper_id = str(record.get("paper_id", "P000"))
    try:
        return int(paper_id[1:])
    except ValueError:
        return 0


def collect_metadata_records(config: ProjectConfig) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    if not config.metadata_root.exists():
        return records
    for path in sorted(config.metadata_root.glob("P*.yaml")):
        errors = validate_metadata_record(path)
        if errors:
            joined = "; ".join(errors)
            raise IndexError(f"元数据无效，无法生成索引: {path}: {joined}")
        records.append(load_metadata_record(path))
    return records


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    return str(value)


def render_paper_index(records: list[dict[str, Any]]) -> str:
    columns = ["paper_id", "year", "title", "venue", "decision", "used_for", "pdf_status"]
    lines = [
        "# 文献索引",
        "",
        "正式事实源是 `metadata/P###.yaml`；本文件只作为人工阅读索引，应由 `rsa regenerate-index` 生成。",
        "",
        "| paper_id | year | title | venue | decision | used_for | pdf_status |",
        "|----------|------|-------|-------|----------|----------|------------|",
    ]
    for record in sorted(records, key=_paper_sort_key):
        values = [_cell(record.get(column)).replace("|", "\\|") for column in columns]
        lines.append("| " + " | ".join(values) + " |")
    lines.extend(
        [
            "",
            "## 字段说明",
            "",
            "- `paper_id`: 正式文献编号。",
            "- `year`: 发表年份。",
            "- `title`: 论文标题。",
            "- `venue`: 期刊、会议或预印本平台。",
            "- `decision`: 人工收录决策。",
            "- `used_for`: 计划用于的章节、问题、实验或对比。",
            "- `pdf_status`: PDF 获取与授权状态。",
            "",
        ]
    )
    return "\n".join(lines)


def generate_paper_index(config: ProjectConfig) -> str:
    return render_paper_index(collect_metadata_records(config))


def validate_paper_index(config: ProjectConfig) -> list[str]:
    expected = generate_paper_index(config)
    if not config.paper_index_path.exists():
        return [
            f"paper_index.md 不存在，请运行 rsa --root {config.root} regenerate-index"
        ]
    current = config.paper_index_path.read_text(encoding="utf-8")
    if current != expected:
        return [
            "paper_index.md 与 metadata/P###.yaml 不一致；请确认后运行 rsa regenerate-index 显式重建。"
        ]
    return []


def regenerate_paper_index(config: ProjectConfig) -> Path:
    config.paper_index_path.parent.mkdir(parents=True, exist_ok=True)
    config.paper_index_path.write_text(generate_paper_index(config), encoding="utf-8")
    return config.paper_index_path
