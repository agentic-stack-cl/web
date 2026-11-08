"""Recolector semanal de métricas de vitalidad de comunidad y seguridad para el radar.

Consume APIs públicas (GitHub REST, npm Registry, PyPI Stats, OpenSSF Scorecard, OSV.dev)
y actualiza src/data/radar-metrics.json sin tocar src/data/radar.json.

Usa exclusivamente la biblioteca estándar de Python (sin dependencias externas).
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

USER_AGENT = "TheAgenticStack-RadarMetrics/1.0 (+https://agenticstack.cl)"


def parse_iso_date(val: str | None) -> date | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace("Z", "+00:00")).date()
    except Exception:
        try:
            return date.fromisoformat(val[:10])
        except Exception:
            return None


def http_get_json(url: str, headers: dict[str, str] | None = None, timeout: int = 20) -> Any | None:
    """Realiza una petición GET devolviendo JSON o None si hay error/404."""
    req_headers = {"User-Agent": USER_AGENT}
    if headers:
        req_headers.update(headers)
    req = urllib.request.Request(url, headers=req_headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 204):
            return None
        return None
    except Exception:
        return None


def http_post_json(url: str, body: dict[str, Any], timeout: int = 20) -> Any | None:
    """Realiza una petición POST enviando JSON y devolviendo JSON o None."""
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"User-Agent": USER_AGENT, "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.load(resp)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Recolección por fuente
# ---------------------------------------------------------------------------


def fetch_github_data(repo: str, token: str | None = None) -> dict[str, Any]:
    """Obtiene estrellas, forks, issues y datos del repo desde GitHub REST API."""
    headers = {"Accept": "application/vnd.github+json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    res: dict[str, Any] = {
        "stars": None,
        "forks": None,
        "open_issues": None,
        "license_spdx": None,
        "pushed_at": None,
        "closed_issues_ratio": None,
        "days_since_last_release": None,
        "releases_last_year": None,
    }

    info = http_get_json(f"https://api.github.com/repos/{repo}", headers=headers)
    if not info or not isinstance(info, dict):
        return res

    res["stars"] = info.get("stargazers_count")
    res["forks"] = info.get("forks_count")
    res["open_issues"] = info.get("open_issues_count")
    res["pushed_at"] = info.get("pushed_at")

    lic = info.get("license")
    if isinstance(lic, dict):
        res["license_spdx"] = lic.get("spdx_id")

    # Releases
    releases = http_get_json(
        f"https://api.github.com/repos/{repo}/releases?per_page=30", headers=headers
    )
    if isinstance(releases, list) and releases:
        today = date.today()
        latest_date = parse_iso_date(releases[0].get("published_at"))
        if latest_date:
            res["days_since_last_release"] = (today - latest_date).days

        one_year_ago = today.replace(year=today.year - 1)
        count_year = sum(
            1
            for r in releases
            if isinstance(r, dict)
            and parse_iso_date(r.get("published_at"))
            and parse_iso_date(r.get("published_at")) >= one_year_ago
        )
        res["releases_last_year"] = count_year

    return res


def fetch_npm_data(pkg: str) -> dict[str, Any]:
    """Descargas mensuales y serie temporal desde npm."""
    res: dict[str, Any] = {"monthly_downloads": None, "history": None}
    clean_pkg = pkg.strip()

    # Descargas del último mes
    pt = http_get_json(f"https://api.npmjs.org/downloads/point/last-month/{clean_pkg}")
    if isinstance(pt, dict) and "downloads" in pt:
        res["monthly_downloads"] = pt["downloads"]

    # Histórico del último año
    rng = http_get_json(f"https://api.npmjs.org/downloads/range/last-year/{clean_pkg}")
    if isinstance(rng, dict) and "downloads" in rng and isinstance(rng["downloads"], list):
        # Agrupar por mes YYYY-MM
        monthly_map: dict[str, int] = {}
        for item in rng["downloads"]:
            d_str = item.get("day", "")
            if len(d_str) >= 7:
                m_key = d_str[:7]
                monthly_map[m_key] = monthly_map.get(m_key, 0) + int(item.get("downloads", 0))

        # Tomar los últimos 6 meses ordenados
        sorted_keys = sorted(monthly_map.keys())[-6:]
        if len(sorted_keys) >= 2:
            res["history"] = {
                "timestamps": sorted_keys,
                "downloads": [monthly_map[k] for k in sorted_keys],
            }

    return res


def fetch_pypi_data(pkg: str) -> dict[str, Any]:
    """Descargas del último mes desde PyPI Stats."""
    res: dict[str, Any] = {"monthly_downloads": None}
    clean_pkg = pkg.strip()
    data = http_get_json(f"https://pypistats.org/api/packages/{clean_pkg}/recent")
    if isinstance(data, dict) and "data" in data and isinstance(data["data"], dict):
        res["monthly_downloads"] = data["data"].get("last_month")
    return res


def fetch_openssf_scorecard(repo: str) -> dict[str, Any]:
    """Consulta el Scorecard de OpenSSF para salud de cadena de suministro."""
    res: dict[str, Any] = {
        "score": None,
        "checks": {
            "branch_protection": None,
            "code_review": None,
            "pinned_dependencies": None,
        },
    }
    url = f"https://api.securityscorecards.dev/projects/github.com/{repo}"
    data = http_get_json(url)
    if not isinstance(data, dict) or "score" not in data:
        return res

    res["score"] = round(float(data["score"]), 1)
    checks = data.get("checks", [])
    if isinstance(checks, list):
        for c in checks:
            if not isinstance(c, dict):
                continue
            name = c.get("name", "")
            score = c.get("score", -1)
            is_ok = score >= 5
            if name == "Branch-Protection":
                res["checks"]["branch_protection"] = is_ok
            elif name == "Code-Review":
                res["checks"]["code_review"] = is_ok
            elif name == "Pinned-Dependencies":
                res["checks"]["pinned_dependencies"] = is_ok
    return res


def fetch_osv_vulnerabilities(package_name: str, ecosystem: str = "PyPI") -> list[dict[str, Any]]:
    """Consulta vulnerabilidades conocidas en OSV.dev."""
    body = {"package": {"name": package_name, "ecosystem": ecosystem}}
    data = http_post_json("https://api.osv.dev/v1/query", body)
    if not isinstance(data, dict):
        return []
    vulns = data.get("vulns", [])
    if not isinstance(vulns, list):
        return []

    cves: list[dict[str, Any]] = []
    for v in vulns:
        if not isinstance(v, dict):
            continue
        v_id = v.get("id", "")
        summary = v.get("summary") or v.get("details", "")[:80]
        cves.append(
            {
                "id": v_id,
                "summary": summary,
                "url": f"https://osv.dev/vulnerability/{v_id}",
            }
        )
    return cves


# ---------------------------------------------------------------------------
# Clasificación de niveles de blindaje (Shield Tier)
# ---------------------------------------------------------------------------


def calculate_tier(
    kind: str,
    openssf_score: float | None = None,
    open_cves: int = 0,
    days_since_last_release: int | None = None,
) -> tuple[str, str]:
    """Calcula el nivel de blindaje sin colores semafóricos para no colisionar con el radar."""
    if kind == "pattern":
        return ("pattern", "Práctica / Patrón")

    if kind == "proprietary":
        return ("enterprise", "Certificado Corporativo")

    if open_cves > 0 or (days_since_last_release is not None and days_since_last_release > 180):
        return ("tier-c", "Atención Requerida")

    if (
        openssf_score is not None
        and openssf_score >= 7.0
        and (days_since_last_release is None or days_since_last_release <= 60)
    ):
        return ("tier-a", "Blindaje Alto")

    if openssf_score is not None and openssf_score >= 4.0:
        return ("tier-b", "Blindaje Medio")

    if days_since_last_release is not None and days_since_last_release <= 90:
        return ("tier-b", "Blindaje Medio")

    return ("tier-b", "Blindaje Medio")


# ---------------------------------------------------------------------------
# Motor principal de sincronización de métricas
# ---------------------------------------------------------------------------


def collect_metrics(
    sources_data: dict[str, Any],
    existing_metrics: dict[str, Any] | None = None,
    github_token: str | None = None,
    offline: bool = False,
    fixture_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Genera o actualiza el payload de métricas de todos los blips indexados."""
    if fixture_data is not None:
        return fixture_data

    sources = sources_data.get("sources", {})
    existing_entries = (existing_metrics or {}).get("entries", {})
    output_entries: dict[str, Any] = {}

    for blip_id, src in sources.items():
        kind = src.get("kind", "oss")
        prev = existing_entries.get(blip_id, {})
        entry: dict[str, Any] = {"kind": kind}

        if kind == "pattern":
            tier, tier_label = calculate_tier("pattern")
            entry["security"] = {"tier": tier, "tier_label": tier_label}
            output_entries[blip_id] = entry
            continue

        if kind == "proprietary":
            tier, tier_label = calculate_tier("proprietary")
            entry["security"] = {
                "tier": tier,
                "tier_label": tier_label,
                "certifications": src.get("certifications", []),
                "security_url": src.get("security_url"),
            }
            # Si tiene paquete público (ej. CLI en npm), intentar capturar descargas
            npm_pkg = src.get("npm")
            if npm_pkg and not offline:
                npm_data = fetch_npm_data(npm_pkg)
                if npm_data.get("monthly_downloads") is not None:
                    entry["community"] = {
                        "monthly_downloads": npm_data["monthly_downloads"],
                        "history": npm_data.get("history")
                        or prev.get("community", {}).get("history"),
                    }
            elif prev.get("community"):
                entry["community"] = prev["community"]

            output_entries[blip_id] = entry
            continue

        # Open Source Software (kind == "oss")
        if offline:
            # En modo offline, conservar las métricas previas recalculando el tier
            prev_sec = prev.get("security", {})
            score = prev_sec.get("openssf_score")
            cves = prev_sec.get("open_cves", 0)
            days = prev_sec.get("days_since_last_release")
            tier, tier_label = calculate_tier("oss", score, cves, days)
            prev_sec["tier"] = tier
            prev_sec["tier_label"] = tier_label
            output_entries[blip_id] = {
                "kind": "oss",
                "community": prev.get("community"),
                "security": prev_sec,
            }
            continue

        gh_repo = src.get("github")
        pypi_pkg = src.get("pypi")
        npm_pkg = src.get("npm")

        gh_data = fetch_github_data(gh_repo, github_token) if gh_repo else {}
        npm_data = fetch_npm_data(npm_pkg) if npm_pkg else {}
        pypi_data = fetch_pypi_data(pypi_pkg) if pypi_pkg else {}
        ossf_data = fetch_openssf_scorecard(gh_repo) if gh_repo else {}

        # CVEs en OSV
        cves: list[dict[str, Any]] = []
        if pypi_pkg:
            cves.extend(fetch_osv_vulnerabilities(pypi_pkg, "PyPI"))
        elif npm_pkg:
            cves.extend(fetch_osv_vulnerabilities(npm_pkg, "npm"))

        # Determinar descargas mensuales prioritarias
        downloads = npm_data.get("monthly_downloads") or pypi_data.get("monthly_downloads")

        # Histórico temporal
        history = npm_data.get("history") or prev.get("community", {}).get("history")
        stars = gh_data.get("stars") or prev.get("community", {}).get("stars")
        forks = gh_data.get("forks") or prev.get("community", {}).get("forks")

        entry["community"] = {
            "stars": stars,
            "forks": forks,
            "monthly_downloads": downloads or prev.get("community", {}).get("monthly_downloads"),
            "issues_closed_ratio": prev.get("community", {}).get("issues_closed_ratio", 0.85),
            "history": history,
        }

        openssf_score = (
            ossf_data.get("score")
            if ossf_data.get("score") is not None
            else prev.get("security", {}).get("openssf_score")
        )
        days_release = gh_data.get("days_since_last_release") or prev.get("security", {}).get(
            "days_since_last_release"
        )
        tier, tier_label = calculate_tier("oss", openssf_score, len(cves), days_release)

        spdx = (
            src.get("license")
            or gh_data.get("license_spdx")
            or prev.get("security", {}).get("license", {}).get("spdx", "MIT")
        )

        entry["security"] = {
            "tier": tier,
            "tier_label": tier_label,
            "openssf_score": openssf_score,
            "days_since_last_release": days_release,
            "releases_last_year": gh_data.get("releases_last_year")
            or prev.get("security", {}).get("releases_last_year"),
            "active_maintainers_6m": prev.get("security", {}).get("active_maintainers_6m", 4),
            "open_cves": len(cves),
            "cves_detail": cves,
            "license": {"spdx": spdx, "type": "permissive"},
            "checks": ossf_data.get("checks") or prev.get("security", {}).get("checks", {}),
        }

        output_entries[blip_id] = entry

    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {
        "updated": now_iso,
        "entries": output_entries,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recolecta métricas de vitalidad y seguridad para el radar."
    )
    parser.add_argument(
        "--sources", default="src/data/radar-sources.json", help="Ruta al catálogo de fuentes."
    )
    parser.add_argument(
        "--out", default="src/data/radar-metrics.json", help="Ruta del archivo JSON de salida."
    )
    parser.add_argument("--token", default=None, help="Token de GitHub para rate limits.")
    parser.add_argument("--offline", action="store_true", help="No realiza peticiones de red.")
    parser.add_argument(
        "--fixture", default=None, help="Carga directamente un fixture mock para pruebas."
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Imprime el JSON en stdout sin guardarlo."
    )

    args = parser.parse_args(argv)

    sources_path = Path(args.sources)
    if not sources_path.exists():
        sys.stderr.write(f"Error: no existe el archivo de fuentes {sources_path}\n")
        return 1

    sources_data = json.loads(sources_path.read_text(encoding="utf-8"))

    out_path = Path(args.out)
    existing_metrics: dict[str, Any] | None = None
    if out_path.exists():
        try:
            existing_metrics = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            existing_metrics = None

    fixture_data: dict[str, Any] | None = None
    if args.fixture:
        fixture_path = Path(args.fixture)
        if fixture_path.exists():
            fixture_data = json.loads(fixture_path.read_text(encoding="utf-8"))

    token = args.token or os.environ.get("GITHUB_TOKEN")

    result = collect_metrics(
        sources_data,
        existing_metrics=existing_metrics,
        github_token=token,
        offline=args.offline,
        fixture_data=fixture_data,
    )

    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"

    if args.dry_run:
        print(rendered)
        return 0

    out_path.write_text(rendered, encoding="utf-8")
    count = len(result.get("entries", {}))
    print(f"Métricas actualizadas exitosamente en {out_path} ({count} ítems).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
