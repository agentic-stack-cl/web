"""Tests para el recolector de métricas de vitalidad y seguridad (metrics.py)."""

from __future__ import annotations

import json
from pathlib import Path

import metrics


def test_calculate_tier_pattern():
    tier, label = metrics.calculate_tier("pattern")
    assert tier == "pattern"
    assert label == "Práctica / Patrón"


def test_calculate_tier_proprietary():
    tier, label = metrics.calculate_tier("proprietary")
    assert tier == "enterprise"
    assert label == "Certificado Corporativo"


def test_calculate_tier_c_with_active_cves():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=8.5, open_cves=1, days_since_last_release=10
    )
    assert tier == "tier-c"
    assert label == "Atención Requerida"


def test_calculate_tier_c_abandoned_project():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=8.0, open_cves=0, days_since_last_release=200
    )
    assert tier == "tier-c"
    assert label == "Atención Requerida"


def test_calculate_tier_a_healthy():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=7.4, open_cves=0, days_since_last_release=15
    )
    assert tier == "tier-a"
    assert label == "Blindaje Alto"


def test_calculate_tier_c_low_scorecard():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=3.2, open_cves=0, days_since_last_release=10
    )
    assert tier == "tier-c"
    assert label == "Atención Requerida"


def test_calculate_tier_unknown_no_telemetry():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=None, open_cves=0, days_since_last_release=None
    )
    assert tier == "unknown"
    assert label == "Sin telemetría"


def test_calculate_tier_b_moderate():
    tier, label = metrics.calculate_tier(
        "oss", openssf_score=5.5, open_cves=0, days_since_last_release=30
    )
    assert tier == "tier-b"
    assert label == "Blindaje Medio"


def test_collect_metrics_offline():
    mock_sources = {
        "sources": {
            "aider": {"kind": "oss", "github": "paul-gauthier/aider", "license": "Apache-2.0"},
            "claude-code": {"kind": "proprietary", "certifications": ["SOC 2 Type II"]},
            "spec-driven": {"kind": "pattern"},
        }
    }
    mock_prev = {
        "entries": {
            "aider": {
                "community": {"stars": 28000, "monthly_downloads": 150000},
                "security": {"openssf_score": 7.5, "open_cves": 0, "days_since_last_release": 10},
            }
        }
    }

    res = metrics.collect_metrics(mock_sources, existing_metrics=mock_prev, offline=True)
    entries = res.get("entries", {})

    assert "aider" in entries
    assert entries["aider"]["security"]["tier"] == "tier-a"
    assert entries["aider"]["community"]["stars"] == 28000

    assert "claude-code" in entries
    assert entries["claude-code"]["security"]["tier"] == "enterprise"

    assert "spec-driven" in entries
    assert entries["spec-driven"]["security"]["tier"] == "pattern"


def test_collect_metrics_fixture_override():
    fake_fixture = {"updated": "2026-11-08T00:00:00Z", "entries": {"custom": {"kind": "oss"}}}
    res = metrics.collect_metrics({}, fixture_data=fake_fixture)
    assert res == fake_fixture


def test_cli_missing_sources(tmp_path: Path):
    non_existent = tmp_path / "does_not_exist.json"
    exit_code = metrics.main(["--sources", str(non_existent)])
    assert exit_code == 1


def test_cli_dry_run(capsys, tmp_path: Path):
    sources_file = tmp_path / "sources.json"
    sources_file.write_text(
        json.dumps({"sources": {"test-item": {"kind": "pattern"}}}), encoding="utf-8"
    )

    exit_code = metrics.main(["--sources", str(sources_file), "--dry-run", "--offline"])
    assert exit_code == 0

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "test-item" in data["entries"]
    assert data["entries"]["test-item"]["security"]["tier"] == "pattern"
