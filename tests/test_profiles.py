from pathlib import Path

from rsa_cli.cli import main
from rsa_cli.profiles import validate_topic_profile


VALID_PROFILE = """
topic_id: test_topic
topic_name: Test Topic
core_keywords:
  - keyword
priority_questions:
  - What is the question?
important_metrics:
  - metric
preferred_sources:
  - official source
exclude_scope:
  - excluded item
grade_rules:
  A:
    description: Core evidence
    criteria:
      - Directly relevant
  B:
    description: Supporting evidence
    criteria:
      - Related
  C:
    description: Peripheral evidence
    criteria:
      - Weakly related
  Reject:
    description: Out of scope
    criteria:
      - Not relevant
required_outputs:
  - final_round_summary.md
"""


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_complete_profile_passes_validation(tmp_path):
    profile = tmp_path / "topic.yaml"
    write(profile, VALID_PROFILE)

    assert validate_topic_profile(profile) == []


def test_missing_fields_are_reported_together(tmp_path):
    profile = tmp_path / "topic.yaml"
    write(
        profile,
        """
topic_id: incomplete
topic_name: Incomplete
""",
    )

    errors = validate_topic_profile(profile)

    for field in [
        "core_keywords",
        "priority_questions",
        "important_metrics",
        "preferred_sources",
        "exclude_scope",
        "grade_rules",
        "required_outputs",
    ]:
        assert f"missing required field: {field}" in errors


def test_invalid_yaml_returns_actionable_cli_error(tmp_path, capsys):
    profile = tmp_path / "broken.yaml"
    write(profile, "topic_id: [\n")

    exit_code = main(["validate-profile", str(profile)])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "invalid YAML" in captured.err
    assert "Traceback" not in captured.err


def test_starter_profile_passes_generic_validation():
    repo_root = Path(__file__).resolve().parents[1]
    starter = (
        repo_root
        / "01_literature"
        / "topic_profiles"
        / "sar_noncontinuous_aperture.yaml"
    )

    assert validate_topic_profile(starter) == []


def test_cli_validates_starter_profile(capsys):
    repo_root = Path(__file__).resolve().parents[1]
    starter = (
        repo_root
        / "01_literature"
        / "topic_profiles"
        / "sar_noncontinuous_aperture.yaml"
    )

    exit_code = main(["validate-profile", str(starter)])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Profile valid" in captured.out
