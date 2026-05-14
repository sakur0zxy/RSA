import io
import json
from pathlib import Path

import pytest
import yaml

from rsa_cli.acquisition import (
    AcquisitionError,
    candidate_status,
    discover_source_candidates,
    download_best_candidate,
    download_candidate,
    download_direct_url,
    find_sources,
    validate_candidate_record,
    validate_custom_providers,
)
from rsa_cli.assets import validate_source_record
from rsa_cli.config import load_project_config
from rsa_cli.metadata import write_metadata_record
from rsa_cli.skeleton import create_literature_skeleton


def metadata_values(**overrides):
    values = {
        "title": "Authorized Acquisition Paper",
        "authors": ["Ada Lovelace"],
        "year": "2024",
        "venue": "Journal of Tests",
        "doi": "10.1234/acquisition",
        "official_url": None,
        "source_reliability": "publisher",
        "decision": "include",
        "decision_reason": "用于测试授权获取。",
        "last_checked": "2026-05-14",
        "pdf_status": "not_acquired",
        "local_pdf": None,
        "assets": [],
        "topic_profile": "demo",
        "priority_questions": ["Q1"],
        "used_for": ["自动获取"],
        "research_roles": ["method"],
        "notes": "人工备注",
    }
    values.update(overrides)
    return values


def prepare_project(tmp_path: Path, **metadata_overrides):
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(**metadata_overrides),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    return config


def write_pdf(path: Path, text: str = "test pdf") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"%PDF-1.4\n" + text.encode("utf-8"))
    return path


def test_discover_candidates_from_official_pdf_is_read_only_valid(tmp_path):
    pdf = write_pdf(tmp_path / "official.pdf")
    config = prepare_project(tmp_path, official_url=pdf.as_uri())

    path = discover_source_candidates(config, "P001")

    assert path == config.source_candidates_root / "P001.yaml"
    assert validate_candidate_record(config, "P001") == []
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    official = [item for item in data["candidates"] if item["provider_id"] == "official_url"][0]
    assert official["match_basis"] == "official_url"
    assert official["approved_for_download"] is True
    assert official["reason_zh"]


def test_title_only_candidate_cannot_auto_download(tmp_path):
    config = prepare_project(tmp_path, doi=None, official_url="https://example.org/landing")

    path = discover_source_candidates(config, "P001", provider_filter="missing")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert data["candidates"][0]["match_basis"] == "title_only"
    assert data["candidates"][0]["approved_for_download"] is False
    assert data["candidates"][0]["status"] == "blocked"
    assert validate_candidate_record(config, "P001") == []


def test_custom_provider_schema_success_and_bypass_rejection(tmp_path):
    (tmp_path / ".rsa").mkdir()
    (tmp_path / ".rsa" / "local.yaml").write_text(
        """
source_discovery:
  custom_providers:
    - provider_id: university_library
      enabled: true
      name_zh: 学校图书馆数据库
      provider_type: database_search
      base_url: https://library.example.edu
      query_mode: url_template
      query_template: https://library.example.edu/search?q={title}
      allowed_domains:
        - library.example.edu
      allowed_result_types:
        - database_record
        - publisher_page
      access_mode: institutional_subscription
      requires_login: true
      user_access_confirmed: true
      authorization_policy: institutional_subscription
      usage_restriction_zh: 仅供个人科研阅读，不得公开分发 PDF。
      notes_zh: 用户通过学校账号或机构订阅访问；RSA 不保存账号密码。
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    assert validate_custom_providers(config) == []

    (tmp_path / ".rsa" / "local.yaml").write_text(
        """
source_discovery:
  custom_providers:
    - provider_id: bad
      enabled: true
      name_zh: bad
      provider_type: database_search
      base_url: https://sci-hub.example
      query_mode: url_template
      query_template: https://sci-hub.example/{doi}
      allowed_domains: [sci-hub.example]
      allowed_result_types: [pdf]
      access_mode: direct_access
      requires_login: false
      user_access_confirmed: true
      authorization_policy: direct_access
      usage_restriction_zh: 仅供个人科研阅读。
      notes_zh: sci-hub mirror
""",
        encoding="utf-8",
    )
    config = load_project_config(tmp_path)
    errors = validate_custom_providers(config)
    assert any("Sci-Hub" in error for error in errors)


def write_browser_provider(tmp_path: Path, *, query_template: str | None = None) -> None:
    (tmp_path / ".rsa").mkdir(exist_ok=True)
    (tmp_path / ".rsa" / "local.yaml").write_text(
        f"""
source_discovery:
  custom_providers:
    - provider_id: library_browser
      enabled: true
      name_zh: 学校图书馆浏览器会话
      provider_type: browser_session
      base_url: https://library.example.edu
      login_url: https://library.example.edu/login
      session_storage: .rsa/sessions/library_browser.storage_state.json
      session_required: true
      query_mode: url_template
      query_template: {query_template or "https://library.example.edu/papers/{doi}.pdf"}
      allowed_domains:
        - library.example.edu
      allowed_result_types:
        - pdf
      access_mode: institutional_subscription
      requires_login: true
      user_access_confirmed: true
      authorization_policy: user_authorized_access
      usage_restriction_zh: 仅供个人科研阅读，不得公开分发 PDF。
      notes_zh: 用户通过学校账号自行登录；RSA 不保存账号密码。
""",
        encoding="utf-8",
    )


def write_browser_state(tmp_path: Path, *, domain: str = "library.example.edu") -> None:
    session = tmp_path / ".rsa" / "sessions" / "library_browser.storage_state.json"
    session.parent.mkdir(parents=True, exist_ok=True)
    session.write_text(
        json.dumps(
            {
                "cookies": [
                    {
                        "name": "LIBSESSION",
                        "value": "cookie-value",
                        "domain": domain,
                        "path": "/",
                    }
                ],
                "origins": [],
            }
        ),
        encoding="utf-8",
    )


class FakePdfResponse(io.BytesIO):
    def __enter__(self):
        return self

    def __exit__(self, *_args):
        self.close()
        return False


def test_browser_session_provider_without_session_creates_blocked_candidate(tmp_path):
    write_browser_provider(tmp_path)
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    path = discover_source_candidates(config, "P001", provider_filter="library_browser")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    candidate = data["candidates"][0]
    assert candidate["provider_type"] == "browser_session"
    assert candidate["status"] == "blocked"
    assert "尚未登录" in candidate["reason_zh"]
    assert validate_candidate_record(config, "P001") == []


def test_browser_session_provider_download_reuses_matching_cookie(tmp_path, monkeypatch):
    write_browser_provider(tmp_path)
    write_browser_state(tmp_path)
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    seen_cookie = {}

    def fake_urlopen(request, timeout=30):
        seen_cookie["value"] = request.get_header("Cookie")
        assert timeout == 30
        return FakePdfResponse(b"%PDF-1.4\nsession pdf")

    monkeypatch.setattr("rsa_cli.acquisition.urllib.request.urlopen", fake_urlopen)

    result = find_sources(config, "P001", provider_filter="library_browser")

    assert result.downloaded_count == 1
    assert seen_cookie["value"] == "LIBSESSION=cookie-value"
    assert validate_candidate_record(config, "P001") == []
    assert validate_source_record(config, "P001") == []


def test_browser_session_download_fails_closed_without_matching_cookie(tmp_path):
    write_browser_provider(tmp_path)
    write_browser_state(tmp_path, domain="other.example.edu")
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )
    discover_source_candidates(config, "P001", provider_filter="library_browser")

    with pytest.raises(AcquisitionError, match="没有匹配目标域名"):
        download_best_candidate(config, "P001")


def test_browser_session_provider_disallowed_domain_is_blocked(tmp_path):
    write_browser_provider(tmp_path, query_template="https://evil.example/papers/{doi}.pdf")
    write_browser_state(tmp_path)
    config = load_project_config(tmp_path)
    create_literature_skeleton(config)
    write_metadata_record(
        config,
        metadata_values(),
        human_confirmed=True,
        confirmed_by="zxy",
    )

    path = discover_source_candidates(config, "P001", provider_filter="library_browser")

    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    candidate = data["candidates"][0]
    assert candidate["status"] == "blocked"
    assert "allowed_domains" in candidate["reason_zh"]


def test_find_sources_default_downloads_approved_candidate(tmp_path):
    pdf = write_pdf(tmp_path / "official.pdf")
    config = prepare_project(tmp_path, official_url=pdf.as_uri())

    result = find_sources(config, "P001")

    assert result.downloaded_count == 1
    assert candidate_status(config, "P001").downloaded_count == 1
    assert validate_candidate_record(config, "P001") == []
    assert validate_source_record(config, "P001") == []
    sources = yaml.safe_load((config.sources_root / "P001.yaml").read_text(encoding="utf-8"))
    assert sources["sources"][0]["sha256"]
    assert sources["sources"][0]["is_primary"] is True


def test_find_sources_no_download_creates_candidates_only(tmp_path):
    pdf = write_pdf(tmp_path / "official.pdf")
    config = prepare_project(tmp_path, official_url=pdf.as_uri())

    result = find_sources(config, "P001", auto_download=False)

    assert result.candidates_found >= 1
    assert result.downloaded_count == 0
    assert not (config.sources_root / "P001.yaml").exists()


def test_duplicate_download_records_duplicate_without_overwrite(tmp_path):
    pdf = write_pdf(tmp_path / "official.pdf")
    config = prepare_project(tmp_path, official_url=pdf.as_uri())
    discover_source_candidates(config, "P001")
    first = download_best_candidate(config, "P001")
    record = yaml.safe_load((config.source_candidates_root / "P001.yaml").read_text(encoding="utf-8"))
    downloaded = [item for item in record["candidates"] if item["status"] == "downloaded"][0]
    downloaded["status"] = "approved_for_download"
    downloaded["approved_for_download"] = True
    candidate_id = downloaded["candidate_id"]
    (config.source_candidates_root / "P001.yaml").write_text(
        yaml.safe_dump(record, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    duplicate = download_candidate(config, "P001", candidate_id)

    assert first.status == "downloaded"
    assert duplicate.status == "duplicate"
    assert duplicate.sha256 == first.sha256
    sources = yaml.safe_load((config.sources_root / "P001.yaml").read_text(encoding="utf-8"))
    assert len(sources["sources"]) == 1


def test_direct_url_requires_authorization_fields(tmp_path):
    pdf = write_pdf(tmp_path / "manual.pdf")
    config = prepare_project(tmp_path)

    try:
        download_direct_url(
            config,
            "P001",
            url=pdf.as_uri(),
            authorization_mode="unknown",
            access_mode="direct_access",
            usage_restriction_zh="仅供个人科研阅读。",
        )
    except AcquisitionError as exc:
        assert "authorization_mode" in str(exc)
    else:
        raise AssertionError("expected AcquisitionError")

    result = download_direct_url(
        config,
        "P001",
        url=pdf.as_uri(),
        authorization_mode="direct_access",
        access_mode="direct_access",
        usage_restriction_zh="仅供个人科研阅读，不得公开分发 PDF。",
    )

    assert result.status == "downloaded"


def test_failed_download_cleans_tmp_and_records_failed_candidate(tmp_path):
    bad_pdf = tmp_path / "bad.pdf"
    bad_pdf.write_text("not a pdf", encoding="utf-8")
    config = prepare_project(tmp_path, official_url=bad_pdf.as_uri())
    discover_source_candidates(config, "P001")

    try:
        download_best_candidate(config, "P001")
    except AcquisitionError as exc:
        assert "不是 PDF" in str(exc)
    else:
        raise AssertionError("expected AcquisitionError")

    assert not list((config.pdfs_root / "P001").glob("*.tmp"))
    record = yaml.safe_load((config.source_candidates_root / "P001.yaml").read_text(encoding="utf-8"))
    failed = [item for item in record["candidates"] if item["provider_id"] == "official_url"][0]
    assert failed["status"] == "failed"


def test_multi_version_primary_selection_prefers_publisher_version(tmp_path):
    first_pdf = write_pdf(tmp_path / "repo.pdf", "repo")
    second_pdf = write_pdf(tmp_path / "publisher.pdf", "publisher")
    config = prepare_project(tmp_path)

    download_direct_url(
        config,
        "P001",
        url=first_pdf.as_uri(),
        authorization_mode="open_access",
        access_mode="open_access",
        usage_restriction_zh="仅供个人科研阅读。",
        version_label="repository_copy",
    )
    download_direct_url(
        config,
        "P001",
        url=second_pdf.as_uri(),
        authorization_mode="direct_access",
        access_mode="direct_access",
        usage_restriction_zh="仅供个人科研阅读。",
        version_label="publisher_version",
    )

    sources = yaml.safe_load((config.sources_root / "P001.yaml").read_text(encoding="utf-8"))
    primary = [source for source in sources["sources"] if source["is_primary"]][0]
    assert primary["version_label"] == "publisher_version"
