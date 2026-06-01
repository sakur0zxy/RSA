import base64
import json
import time
from pathlib import Path

import pytest

from rsa_cli.codex_oauth import (
    CodexOAuthError,
    call_codex_responses,
    clear_codex_oauth_auth,
    codex_oauth_status,
    import_codex_cli_auth,
)
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.notes import load_reading_note
from rsa_cli.reading_draft import DraftError, draft_reading_note
from rsa_cli.skeleton import create_literature_skeleton


def fake_jwt(exp: int | None = None) -> str:
    payload = {"https://api.openai.com/auth.chatgpt_account_id": "acc_test"}
    if exp is not None:
        payload["exp"] = exp
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).rstrip(b"=")
    return "header." + encoded.decode("ascii") + ".signature"


def write_codex_auth(codex_home: Path, *, exp: int | None = None) -> None:
    codex_home.mkdir(parents=True, exist_ok=True)
    (codex_home / "auth.json").write_text(
        json.dumps(
            {
                "auth_mode": "chatgpt",
                "tokens": {
                    "access_token": fake_jwt(exp),
                    "refresh_token": "refresh-secret",
                    "id_token": "id-secret",
                    "account_id": "acc_test",
                },
            }
        ),
        encoding="utf-8",
    )


def write_local_config(root: Path, codex_home: Path, *, token_source: str = "rsa_store") -> None:
    local = root / ".rsa" / "local.yaml"
    local.parent.mkdir(parents=True, exist_ok=True)
    local.write_text(
        f"""
reading_draft:
  llm:
    provider: codex_oauth
    model: gpt-test
    timeout_seconds: 5
    codex_oauth:
      codex_home: "{codex_home.as_posix()}"
      token_source: "{token_source}"
      response_endpoint: "https://example.invalid/responses"
""",
        encoding="utf-8",
    )


def metadata_values(local_pdf: str) -> dict:
    return {
        "title": "Codex OAuth Paper",
        "authors": ["Ada Lovelace"],
        "year": "2026",
        "venue": "Journal of Tests",
        "doi": "10.1234/codex-oauth",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试 Codex OAuth reading draft。",
        "last_checked": "2026-05-30",
        "pdf_status": "local",
        "local_pdf": local_pdf,
        "assets": [],
        "topic_profile": "sar_noncontinuous_aperture",
        "priority_questions": ["Q1"],
        "used_for": ["reading draft"],
        "research_roles": ["method"],
        "notes": "测试记录",
    }


def valid_llm_payload() -> dict:
    return {
        "research_problem_zh": "论文围绕测试问题展开。",
        "method_summary_zh": "方法摘要来自授权全文片段。",
        "experiment_summary_zh": "实验摘要需要人工复核。",
        "dataset_or_scene_zh": "数据或场景需要人工复核。",
        "metrics_zh": "指标需要人工复核。",
        "main_findings_zh": "主要发现只是 staging 草稿。",
        "limitations_zh": "局限性需要人工复核。",
        "topic_relevance_zh": "与当前主题存在候选相关性。",
        "uncertain_points_zh": ["自动草稿需要人工确认。"],
        "source_grounded_claims": [
            {
                "claim_zh": "该论文包含一个可回源的候选判断。",
                "evidence_page": 1,
                "evidence_section": "unknown",
                "source_chunk_id": "C001",
                "evidence_snippet": "gapped aperture SAR reconstruction experiment",
                "needs_human_check": True,
            }
        ],
        "short_quotes": [
            {
                "quote": "gapped aperture SAR reconstruction experiment",
                "page": 1,
                "section": "unknown",
                "reason_zh": "用于定位原文。",
            }
        ],
        "asset_suggestions": [],
    }


def prepare_note_project(tmp_path: Path, codex_home: Path):
    write_local_config(tmp_path, codex_home)
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    source = tmp_path / "codex-oauth-source.pdf"
    source.write_text(
        ("gapped aperture SAR reconstruction experiment with metrics and baseline. ") * 10,
        encoding="utf-8",
    )
    write_metadata_record(
        config,
        metadata_values(str(source)),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    return load_project_config(tmp_path), source


def test_codex_oauth_import_status_and_clear_are_local_only(tmp_path):
    codex_home = tmp_path / "codex_home"
    write_codex_auth(codex_home, exp=int(time.time()) + 3600)
    write_local_config(tmp_path, codex_home)
    config = load_project_config(tmp_path)

    result = import_codex_cli_auth(config)
    assert result.auth_store_path == tmp_path / ".rsa" / "auth" / "codex_oauth.yaml"
    assert result.auth_store_path.exists()
    assert "access_token" in result.auth_store_path.read_text(encoding="utf-8")
    status = codex_oauth_status(config)
    cleared = clear_codex_oauth_auth(config)
    status_after_clear = codex_oauth_status(config)

    assert status.status == "ok"
    assert status.logged_in is True
    assert cleared == result.auth_store_path
    assert not cleared.exists()
    assert status_after_clear.status == "blocked"
    assert "import" in status_after_clear.repair_hint_zh


def test_codex_oauth_import_rejects_expired_token(tmp_path):
    codex_home = tmp_path / "codex_home"
    write_codex_auth(codex_home, exp=int(time.time()) - 3600)
    write_local_config(tmp_path, codex_home)
    config = load_project_config(tmp_path)

    with pytest.raises(CodexOAuthError, match="过期"):
        import_codex_cli_auth(config)

    assert not (tmp_path / ".rsa" / "auth" / "codex_oauth.yaml").exists()


def test_call_codex_responses_parses_output_text_without_printing_tokens(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex_home"
    write_codex_auth(codex_home, exp=int(time.time()) + 3600)
    write_local_config(tmp_path, codex_home)
    config = load_project_config(tmp_path)
    import_codex_cli_auth(config)

    class FakeResponse:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self):
            return json.dumps({"output_text": "{\"ok\": true}"}).encode("utf-8")

    def fake_urlopen(request, timeout):
        assert timeout == 5
        assert request.get_header("Authorization", "").startswith("Bearer ")
        return FakeResponse()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)

    assert call_codex_responses(config, "prompt") == "{\"ok\": true}"


def test_draft_reading_note_codex_oauth_missing_auth_blocks_without_note(tmp_path):
    codex_home = tmp_path / "codex_home"
    config, source = prepare_note_project(tmp_path, codex_home)

    with pytest.raises(DraftError, match="Codex OAuth"):
        draft_reading_note(config, "P001", source_file=str(source))

    assert not (config.notes_root / "P001_reading_note.md").exists()
    assert (config.extracted_root / "P001" / "prompt_packet.yaml").exists()


def test_draft_reading_note_codex_oauth_uses_provider_payload(tmp_path, monkeypatch):
    codex_home = tmp_path / "codex_home"
    write_codex_auth(codex_home, exp=int(time.time()) + 3600)
    config, source = prepare_note_project(tmp_path, codex_home)
    import_codex_cli_auth(config)

    def fake_call(config, prompt, *, system_prompt=None):
        assert "chunks" in prompt
        assert "JSON" in system_prompt
        return json.dumps(valid_llm_payload(), ensure_ascii=False)

    monkeypatch.setattr("rsa_cli.codex_oauth.call_codex_responses", fake_call)

    result = draft_reading_note(config, "P001", source_file=str(source))
    note = load_reading_note(config, "P001")

    assert result.note_status == "ready_for_review"
    assert note.frontmatter["llm_provider"] == "codex_oauth"
    assert note.frontmatter["human_confirmed"] is False
