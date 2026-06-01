import yaml

from rsa_cli.config import load_project_config
from rsa_cli.discovery import (
    DiscoveryError,
    create_discovery_profile,
    export_discovery_to_campaign,
    run_discovery,
    search_discovery,
    validate_discovery,
)
from rsa_cli.skeleton import create_literature_skeleton


def prepare_project(root):
    config = load_project_config(root)
    create_literature_skeleton(config)
    return config


def test_create_discovery_profile_from_research_plan_is_chinese_first(tmp_path):
    config = prepare_project(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text(
        """
# 研究计划

Q1: How can missing aperture samples affect reconstruction artifacts?

We need papers about inverse problems, sparse recovery, imaging metrics, and robust evaluation.
""",
        encoding="utf-8",
    )

    result = create_discovery_profile(
        config,
        plan_file=str(plan),
        topic_profile="sar_noncontinuous_aperture",
        max_queries=2,
    )
    profile = yaml.safe_load(result.profile_path.read_text(encoding="utf-8"))
    queries = yaml.safe_load(result.query_bundle_path.read_text(encoding="utf-8"))

    assert result.discovery_id == "DR001"
    assert result.query_count == 2
    assert profile["formal_write_allowed"] is False
    assert "field_explanations_zh" in profile
    assert "provider_plugins" in profile["future_interfaces"]
    assert queries["queries"][0]["query_id"] == "DQ001"
    assert queries["queries"][0]["reason_zh"]
    assert validate_discovery(config, "DR001") == []


def test_discovery_run_no_search_writes_status_but_no_fake_candidates(tmp_path):
    config = prepare_project(tmp_path)
    plan = tmp_path / "plan.txt"
    plan.write_text("Find work about robust reconstruction and evaluation.", encoding="utf-8")

    result = run_discovery(config, plan_file=str(plan), no_search=True)
    results = yaml.safe_load(result.results_path.read_text(encoding="utf-8"))

    assert result.status == "not_run"
    assert result.candidate_count == 0
    assert results["candidates"] == []
    assert "no-search" in results["reason_zh"]
    assert (tmp_path / "01_literature" / "discovery" / "DR001_report.md").exists()
    assert not list((tmp_path / "01_literature" / "metadata").glob("P*.yaml"))


def test_openalex_results_export_to_campaign_without_formal_write(tmp_path):
    config = prepare_project(tmp_path)
    plan = tmp_path / "plan.md"
    plan.write_text("Need inverse problem reconstruction papers with quantitative metrics.", encoding="utf-8")
    profile = create_discovery_profile(config, plan_file=str(plan), max_queries=1)

    def fake_fetch(url):
        assert "api.openalex.org" in url
        return {
            "results": [
                {
                    "id": "https://openalex.org/W1",
                    "title": "Robust Reconstruction With Quantitative Metrics",
                    "doi": "https://doi.org/10.1234/discovery",
                    "publication_year": 2025,
                    "authorships": [
                        {"author": {"display_name": "Ada Lovelace"}},
                    ],
                    "primary_location": {
                        "landing_page_url": "https://example.org/paper",
                    },
                    "abstract_inverted_index": {
                        "robust": [0],
                        "reconstruction": [1],
                        "metrics": [2],
                    },
                }
            ]
        }

    search = search_discovery(
        config,
        profile.discovery_id,
        provider="openalex",
        max_results=3,
        fetcher=fake_fetch,
    )
    exported = export_discovery_to_campaign(config, profile.discovery_id, created_by="zxy")
    campaign = yaml.safe_load(exported.campaign_path.read_text(encoding="utf-8"))
    results = yaml.safe_load(search.results_path.read_text(encoding="utf-8"))

    assert search.status == "completed"
    assert search.candidate_count == 1
    assert exported.campaign_id == "C001"
    assert campaign["items"][0]["source_candidate_id"] == "DC001"
    assert campaign["items"][0]["status"] == "queued"
    assert campaign["items"][0]["source_row"]["discovery_id"] == profile.discovery_id
    assert results["formal_write_allowed"] is False
    assert "provider_plugins" in results["future_interfaces"]
    assert (tmp_path / "01_literature" / "discovery" / "DR001_report.md").exists()
    assert not list((tmp_path / "01_literature" / "metadata").glob("P*.yaml"))


def test_provider_failure_blocks_without_fake_campaign(tmp_path):
    config = prepare_project(tmp_path)
    profile = create_discovery_profile(
        config,
        objective="Find reliable evaluation literature for reconstruction methods.",
        max_queries=1,
    )

    def failing_fetch(url):
        raise DiscoveryError("network unavailable")

    result = search_discovery(
        config,
        profile.discovery_id,
        provider="openalex",
        fetcher=failing_fetch,
    )
    results = yaml.safe_load(result.results_path.read_text(encoding="utf-8"))

    assert result.status == "blocked"
    assert result.candidate_count == 0
    assert results["search_errors"][0]["error_zh"] == "network unavailable"
    assert not list((tmp_path / "01_literature" / "campaigns").glob("C*.yaml"))
