import pytest
import yaml

from rsa_cli.config import load_project_config
from rsa_cli.evals import (
    EvalError,
    compare_eval_baseline,
    run_eval_fixtures,
    write_eval_baseline,
    write_eval_report,
)
from rsa_cli.skeleton import create_literature_skeleton


def test_eval_fixtures_cover_phase5_failure_modes():
    result = run_eval_fixtures()

    assert result.passed
    assert {case.case_id for case in result.cases} == {
        "metadata_hallucination",
        "unauthorized_pdf_behavior",
        "formal_record_conflict",
        "output_format_drift",
        "scope_creep",
    }


def test_eval_report_baseline_and_compare_are_deterministic(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    result = run_eval_fixtures()

    report_path = write_eval_report(config, result)
    baseline_path = write_eval_baseline(config, result)
    compare = compare_eval_baseline(config)
    baseline = yaml.safe_load(baseline_path.read_text(encoding="utf-8"))

    assert report_path == config.eval_report_path
    assert "metadata_hallucination" in report_path.read_text(encoding="utf-8")
    assert len(baseline["cases"]) == 5
    assert compare.passed
    assert compare.regressions == []
    assert compare.path == config.eval_regression_report_path
    assert "regressions: 0" in compare.path.read_text(encoding="utf-8")


def test_eval_compare_requires_existing_baseline(tmp_path):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)

    with pytest.raises(EvalError):
        compare_eval_baseline(config)
