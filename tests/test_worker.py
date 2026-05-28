from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from rsa_cli.campaign import create_campaign, import_campaign_items
from rsa_cli.cli import main
from rsa_cli.config import load_project_config
from rsa_cli.skeleton import create_literature_skeleton
from rsa_cli.worker import (
    WorkerError,
    add_worker_schedule,
    cancel_worker_task,
    enqueue_due_schedules,
    enqueue_worker_task,
    recover_worker_task,
    run_worker,
    worker_queue_path,
    worker_status,
)


def prepare_project(tmp_path: Path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    return config


def create_queued_campaign(config, tmp_path: Path):
    campaign = create_campaign(
        config,
        name_zh="worker 队列测试",
        objective_zh="验证 Phase 14 worker 只推进 staging/review 自动化。",
    )
    source = tmp_path / "worker_items.yaml"
    source.write_text(
        yaml.safe_dump(
            {
                "items": [
                    {
                        "title": "Worker Candidate Paper",
                        "doi": "10.1234/worker",
                        "year": "2026",
                        "first_author": "Ada",
                    }
                ]
            },
            allow_unicode=True,
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    import_campaign_items(config, campaign.campaign_id, source_file=str(source))
    return campaign


def test_worker_runs_campaign_task_without_formal_write(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_queued_campaign(config, tmp_path)

    enqueued = enqueue_worker_task(config, "campaign-run", campaign.campaign_id)
    result = run_worker(config, max_tasks=1)
    status = worker_status(config)
    queue_data = yaml.safe_load(worker_queue_path(config).read_text(encoding="utf-8"))

    assert enqueued.task_id == "WT001"
    assert result.processed_count == 1
    assert result.completed_count == 1
    assert result.failed_count == 0
    assert status.completed_count == 1
    assert queue_data["tasks"][0]["status"] == "completed"
    assert queue_data["tasks"][0]["formal_write_allowed"] is False
    assert (config.campaigns_root / "C001_metadata_requests.yaml").exists()
    assert not (config.metadata_root / "P001.yaml").exists()
    assert "正式记录仍需人工确认" in queue_data["formal_record_policy_zh"]


def test_worker_schedule_due_enqueues_and_runs_review_queue(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_queued_campaign(config, tmp_path)

    schedule = add_worker_schedule(
        config,
        "campaign-queue",
        campaign.campaign_id,
        interval_hours=1,
    )
    due = enqueue_due_schedules(config)
    run = run_worker(config, max_tasks=1)
    queue_data = yaml.safe_load(worker_queue_path(config).read_text(encoding="utf-8"))

    assert schedule.schedule_id == "WS001"
    assert due.enqueued_count == 1
    assert due.due_schedule_ids == ["WS001"]
    assert run.completed_count == 1
    assert queue_data["tasks"][0]["source"] == "schedule"
    assert queue_data["tasks"][0]["schedule_id"] == "WS001"
    assert (config.campaigns_root / "C001_review_queue.yaml").exists()


def test_worker_cancel_and_recover_state_boundaries(tmp_path):
    config = prepare_project(tmp_path)
    campaign = create_queued_campaign(config, tmp_path)
    enqueue_worker_task(config, "campaign-report", campaign.campaign_id)

    cancelled = cancel_worker_task(config, "WT001", reason_zh="用户暂停测试。")
    with pytest.raises(WorkerError):
        recover_worker_task(config, "WT001")

    queue_path = worker_queue_path(config)
    queue_data = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    queue_data["tasks"][0]["status"] = "running"
    queue_path.write_text(
        yaml.safe_dump(queue_data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    recovered = recover_worker_task(config, "WT001", reason_zh="长任务恢复测试。")

    assert cancelled.status == "cancelled"
    assert recovered.status == "queued"
    updated = yaml.safe_load(queue_path.read_text(encoding="utf-8"))
    assert updated["tasks"][0]["status"] == "queued"
    assert updated["tasks"][0]["started_at"] is None


def test_worker_cli_enqueue_status_run_logs_and_schedule(tmp_path, capsys):
    config = prepare_project(tmp_path)
    create_queued_campaign(config, tmp_path)

    enqueued = main(["--root", str(tmp_path), "worker", "enqueue", "campaign-run", "C001"])
    enqueued_out = capsys.readouterr()
    status = main(["--root", str(tmp_path), "worker", "status"])
    status_out = capsys.readouterr()
    run = main(["--root", str(tmp_path), "worker", "run", "--max-tasks", "1"])
    run_out = capsys.readouterr()
    logs = main(["--root", str(tmp_path), "worker", "logs", "--max-lines", "5"])
    logs_out = capsys.readouterr()
    schedule = main(
        [
            "--root",
            str(tmp_path),
            "worker",
            "schedule",
            "add",
            "campaign-queue",
            "C001",
            "--interval-hours",
            "1",
        ]
    )
    schedule_out = capsys.readouterr()
    due = main(["--root", str(tmp_path), "worker", "schedule", "due"])
    due_out = capsys.readouterr()

    assert enqueued == 0
    assert "WT001" in enqueued_out.out
    assert "正式写入仍需人工确认" in enqueued_out.out
    assert status == 0
    assert "queued=1" in status_out.out
    assert run == 0
    assert "processed=1" in run_out.out
    assert logs == 0
    assert "WT001" in logs_out.out
    assert schedule == 0
    assert "WS001" in schedule_out.out
    assert due == 0
    assert "enqueued=1" in due_out.out
    assert not (config.metadata_root / "P001.yaml").exists()
