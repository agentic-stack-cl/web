#!/usr/bin/env python3
"""Configura el DNS de agenticstack.cl y theagenticstack.cl (Cloudflare) y el dominio en Pages.

Pasos (ver docs/DNS.md):
  python3 scripts/dns/setup.py plan                      # qué haría en Cloudflare (solo lectura)
  python3 scripts/dns/setup.py apply [--github-txt VAL]  # crea zonas, registros y redirección
  python3 scripts/dns/setup.py status                    # estado de zonas, DNS público y Pages
  python3 scripts/dns/setup.py github                    # activa el dominio en Pages y fuerza HTTPS

Variables de entorno:
  CLOUDFLARE_API_TOKEN   token con permisos Zone:Edit, DNS:Edit y Single Redirect:Edit (obligatorio
                         para plan/apply; opcional para status)
  CLOUDFLARE_ACCOUNT_ID  opcional si el token ve una sola cuenta

El script es idempotente: se puede ejecutar varias veces. Nunca imprime el token.
Solo usa la biblioteca estándar de Python (y `gh` para el paso `github`).
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

API = "https://api.cloudflare.com/client/v4"
DOH = "https://cloudflare-dns.com/dns-query"
REPO = "agentic-stack-cl/web"
ORG = "agentic-stack-cl"
MAIN = "agenticstack.cl"
ALIAS = "theagenticstack.cl"
GITHUB_TXT_NAME = f"_github-pages-challenge-{ORG}"
PAGES_A = ["185.199.108.153", "185.199.109.153", "185.199.110.153", "185.199.111.153"]
PAGES_AAAA = [
    "2606:50c0:8000::153",
    "2606:50c0:8001::153",
    "2606:50c0:8002::153",
    "2606:50c0:8003::153",
]
PLACEHOLDER_IP = "192.0.2.1"  # IP de documentación (RFC 5737): Cloudflare responde antes de llegar
REDIRECT_REF = "agenticstack_redirect"


@dataclass(frozen=True)
class Record:
    type: str
    name: str  # "@" para el apex, o el subdominio relativo
    content: str
    proxied: bool = False

    def fqdn(self, zone: str) -> str:
        return zone if self.name == "@" else f"{self.name}.{zone}"


def desired_records(zone: str, github_txt: str | None = None) -> list[Record]:
    if zone == MAIN:
        recs = [Record("A", "@", ip) for ip in PAGES_A]
        recs += [Record("AAAA", "@", ip) for ip in PAGES_AAAA]
        recs.append(Record("CNAME", "www", f"{ORG}.github.io"))
        if github_txt:
            recs.append(Record("TXT", GITHUB_TXT_NAME, github_txt))
        return recs
    if zone == ALIAS:
        return [
            Record("A", "@", PLACEHOLDER_IP, proxied=True),
            Record("A", "www", PLACEHOLDER_IP, proxied=True),
        ]
    raise ValueError(zone)


def redirect_rule() -> dict[str, Any]:
    return {
        "ref": REDIRECT_REF,
        "description": f"{ALIAS} → {MAIN} (301, conserva ruta y query)",
        "expression": f'(http.host eq "{ALIAS}") or (http.host eq "www.{ALIAS}")',
        "action": "redirect",
        "action_parameters": {
            "from_value": {
                "status_code": 301,
                "target_url": {"expression": f'concat("https://{MAIN}", http.request.uri.path)'},
                "preserve_query_string": True,
            }
        },
    }


# ---------------------------------------------------------------------------
# Cliente de Cloudflare
# ---------------------------------------------------------------------------


class CloudflareError(RuntimeError):
    pass


class Cloudflare:
    def __init__(self, token: str):
        self._token = token

    def request(self, method: str, path: str, body: Any = None, query: dict | None = None) -> Any:
        url = f"{API}{path}" + (f"?{urllib.parse.urlencode(query)}" if query else "")
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(
            url,
            data=data,
            method=method,
            headers={"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                payload = json.load(resp)
        except urllib.error.HTTPError as exc:
            try:
                payload = json.load(exc)
            except json.JSONDecodeError:
                payload = {"errors": [{"code": exc.code, "message": exc.reason}]}
            payload["_status"] = exc.code
        if not payload.get("success", False):
            errs = "; ".join(
                f"{e.get('code')}: {e.get('message')}" for e in payload.get("errors", [])
            )
            err = CloudflareError(f"{method} {path} → {errs or 'error desconocido'}")
            err.status = payload.get("_status")  # type: ignore[attr-defined]
            raise err
        return payload["result"]

    def account_id(self) -> str:
        env = os.environ.get("CLOUDFLARE_ACCOUNT_ID")
        if env:
            return env
        accounts = self.request("GET", "/accounts")
        if len(accounts) != 1:
            names = ", ".join(f"{a['name']} ({a['id']})" for a in accounts) or "ninguna"
            raise CloudflareError(
                f"El token ve {len(accounts)} cuentas ({names}). Define CLOUDFLARE_ACCOUNT_ID."
            )
        return accounts[0]["id"]

    def zone(self, name: str) -> dict | None:
        zones = self.request("GET", "/zones", query={"name": name})
        return zones[0] if zones else None

    def create_zone(self, name: str, account: str) -> dict:
        return self.request(
            "POST", "/zones", {"name": name, "account": {"id": account}, "type": "full"}
        )

    def records(self, zone_id: str) -> list[dict]:
        return self.request("GET", f"/zones/{zone_id}/dns_records", query={"per_page": 500})

    def create_record(self, zone_id: str, zone: str, rec: Record) -> None:
        body = {"type": rec.type, "name": rec.fqdn(zone), "content": rec.content, "ttl": 1}
        if rec.type in ("A", "AAAA", "CNAME"):
            body["proxied"] = rec.proxied
        self.request("POST", f"/zones/{zone_id}/dns_records", body)

    def update_proxied(self, zone_id: str, record_id: str, proxied: bool) -> None:
        self.request("PATCH", f"/zones/{zone_id}/dns_records/{record_id}", {"proxied": proxied})

    def delete_record(self, zone_id: str, record_id: str) -> None:
        self.request("DELETE", f"/zones/{zone_id}/dns_records/{record_id}")

    def redirect_ruleset(self, zone_id: str) -> dict | None:
        try:
            return self.request(
                "GET", f"/zones/{zone_id}/rulesets/phases/http_request_dynamic_redirect/entrypoint"
            )
        except CloudflareError as exc:
            if getattr(exc, "status", None) == 404:
                return None
            raise

    def put_redirect(self, zone_id: str, existing: dict | None) -> None:
        rules = [r for r in (existing or {}).get("rules", []) if r.get("ref") != REDIRECT_REF]
        rules = [
            {k: v for k, v in r.items() if k not in ("id", "version", "last_updated")}
            for r in rules
        ]
        rules.append(redirect_rule())
        body = {
            "name": "Redirecciones",
            "kind": "zone",
            "phase": "http_request_dynamic_redirect",
            "rules": rules,
        }
        if existing:
            self.request("PUT", f"/zones/{zone_id}/rulesets/{existing['id']}", body)
        else:
            self.request("POST", f"/zones/{zone_id}/rulesets", body)

    def activation_check(self, zone_id: str) -> None:
        self.request("PUT", f"/zones/{zone_id}/activation_check")


# ---------------------------------------------------------------------------
# Plan de cambios (lógica pura, testeable)
# ---------------------------------------------------------------------------


@dataclass
class Plan:
    create: list[Record]
    fix_proxy: list[tuple[dict, Record]]
    conflicts: list[dict]


def plan_records(zone: str, existing: list[dict], wanted: list[Record]) -> Plan:
    def key(t: str, n: str, c: str) -> tuple[str, str, str]:
        return (t.upper(), n.lower().rstrip("."), c.strip('"').lower().rstrip("."))

    have = {key(r["type"], r["name"], r["content"]): r for r in existing}
    create, fix = [], []
    for rec in wanted:
        k = key(rec.type, rec.fqdn(zone), rec.content)
        if k not in have:
            create.append(rec)
        elif rec.type in ("A", "AAAA", "CNAME") and bool(have[k].get("proxied")) != rec.proxied:
            fix.append((have[k], rec))
    wanted_keys = {key(r.type, r.fqdn(zone), r.content) for r in wanted}
    managed_names = {r.fqdn(zone).lower() for r in wanted if r.type in ("A", "AAAA", "CNAME")}
    conflicts = [
        r
        for r in existing
        if r["type"] in ("A", "AAAA", "CNAME")
        and r["name"].lower() in managed_names
        and key(r["type"], r["name"], r["content"]) not in wanted_keys
    ]
    return Plan(create, fix, conflicts)


def describe(zone: str, plan: Plan) -> list[str]:
    lines = []
    for r in plan.create:
        lines.append(
            f"  + {r.type:5} {r.fqdn(zone):45} {r.content}{'  (proxied)' if r.proxied else ''}"
        )
    for old, r in plan.fix_proxy:
        lines.append(f"  ~ {r.type:5} {old['name']:45} proxied → {r.proxied}")
    for c in plan.conflicts:
        lines.append(
            f"  ! {c['type']:5} {c['name']:45} {c['content']}  (sobra: usa --prune para borrarlo)"
        )
    return lines or ["  = sin cambios"]


# ---------------------------------------------------------------------------
# DNS público (DNS sobre HTTPS, sin depender de dig)
# ---------------------------------------------------------------------------


def resolve(name: str, rtype: str) -> list[str]:
    url = f"{DOH}?{urllib.parse.urlencode({'name': name, 'type': rtype})}"
    req = urllib.request.Request(url, headers={"Accept": "application/dns-json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.load(resp)
    except (urllib.error.URLError, TimeoutError):
        return []
    return sorted(a["data"].rstrip(".").strip('"') for a in data.get("Answer", []))


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def client() -> Cloudflare:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if not token:
        sys.exit("Falta CLOUDFLARE_API_TOKEN. Ver docs/DNS.md (crear el token).")
    return Cloudflare(token)


def cmd_plan_apply(args: argparse.Namespace, apply: bool) -> int:
    cf = client()
    account = cf.account_id()
    nameservers: dict[str, list[str]] = {}
    for zone_name in (MAIN, ALIAS):
        print(f"\n== {zone_name}")
        zone = cf.zone(zone_name)
        if zone is None:
            if not apply:
                print("  + crear zona (plan Free)")
                for line in describe(
                    zone_name, Plan(desired_records(zone_name, args.github_txt), [], [])
                ):
                    print(line)
                if zone_name == ALIAS:
                    print(f"  + regla de redirección 301 → https://{MAIN}")
                continue
            zone = cf.create_zone(zone_name, account)
            print(f"  ✓ zona creada ({zone['id']})")
        else:
            print(f"  = zona existente, estado: {zone['status']}")
        nameservers[zone_name] = zone.get("name_servers", [])

        plan = plan_records(
            zone_name, cf.records(zone["id"]), desired_records(zone_name, args.github_txt)
        )
        for line in describe(zone_name, plan):
            print(line)
        if apply:
            for rec in plan.create:
                cf.create_record(zone["id"], zone_name, rec)
            for old, rec in plan.fix_proxy:
                cf.update_proxied(zone["id"], old["id"], rec.proxied)
            if args.prune:
                for c in plan.conflicts:
                    cf.delete_record(zone["id"], c["id"])
                    print(f"  ✓ borrado {c['type']} {c['name']} {c['content']}")
            if plan.create or plan.fix_proxy:
                print("  ✓ registros aplicados")

        if zone_name == ALIAS:
            existing = cf.redirect_ruleset(zone["id"])
            has = any(r.get("ref") == REDIRECT_REF for r in (existing or {}).get("rules", []))
            if has:
                print(
                    "  = regla de redirección existente (se actualiza al aplicar)"
                    if apply
                    else "  = regla OK"
                )
            else:
                print(f"  + regla de redirección 301 → https://{MAIN}")
            if apply:
                cf.put_redirect(zone["id"], existing)
                print("  ✓ redirección configurada")

    for zone_name in (MAIN, ALIAS):
        if resolve(zone_name, "DS"):
            print(
                f"\n⚠️  {zone_name} tiene DNSSEC activo en NIC Chile (registro DS). "
                "Bórralo en NIC Chile "
                "ANTES de cambiar los servidores DNS, o el dominio dejará de resolver."
            )
    if apply and nameservers:
        print(
            "\n== Siguiente paso: NIC Chile → Mis dominios → Configuración técnica → Servidores DNS"
        )
        for zone_name, ns in nameservers.items():
            print(f"  {zone_name}: {', '.join(ns)}")
    if not args.github_txt:
        print(
            f"\nℹ️  Falta el TXT de verificación de GitHub ({GITHUB_TXT_NAME}.{MAIN}). "
            "Cuando lo tengas, vuelve a ejecutar `apply --github-txt <valor>`."
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    token = os.environ.get("CLOUDFLARE_API_TOKEN")
    if token:
        cf = Cloudflare(token)
        print("== Cloudflare")
        for zone_name in (MAIN, ALIAS):
            zone = cf.zone(zone_name)
            if not zone:
                print(f"  {zone_name}: no existe")
                continue
            print(
                f"  {zone_name}: {zone['status']} · "
                f"NS esperados: {', '.join(zone.get('name_servers', []))}"
            )
            if args.activation_check and zone["status"] == "pending":
                try:
                    cf.activation_check(zone["id"])
                    print("    ↻ revisión de activación solicitada")
                except CloudflareError as exc:
                    print(f"    (no se pudo pedir la revisión: {exc})")

    print("\n== DNS público")
    ok_a = resolve(MAIN, "A") == sorted(PAGES_A)
    checks = [
        (f"NS {MAIN}", ", ".join(resolve(MAIN, "NS")) or "—", None),
        (f"NS {ALIAS}", ", ".join(resolve(ALIAS, "NS")) or "—", None),
        (f"A {MAIN}", ", ".join(resolve(MAIN, "A")) or "—", ok_a),
        (
            f"AAAA {MAIN}",
            ", ".join(resolve(MAIN, "AAAA")) or "—",
            resolve(MAIN, "AAAA") == sorted(PAGES_AAAA),
        ),
        (f"CNAME www.{MAIN}", ", ".join(resolve(f"www.{MAIN}", "CNAME")) or "—", None),
        (
            f"TXT {GITHUB_TXT_NAME}",
            ", ".join(resolve(f"{GITHUB_TXT_NAME}.{MAIN}", "TXT")) or "—",
            None,
        ),
        (f"A {ALIAS}", ", ".join(resolve(ALIAS, "A")) or "—", None),
        (f"DS {MAIN} (DNSSEC en NIC Chile)", ", ".join(resolve(MAIN, "DS")) or "sin DS", None),
    ]
    for label, value, ok in checks:
        mark = "✅" if ok else ("❌" if ok is False else "·")
        print(f"  {mark} {label:50} {value}")

    print("\n== GitHub Pages")
    pages = gh_json(["api", f"repos/{REPO}/pages"])
    if pages:
        cert = (pages.get("https_certificate") or {}).get("state", "—")
        print(
            f"  dominio: {pages.get('cname') or '—'} · certificado: {cert} · "
            f"HTTPS forzado: {pages.get('https_enforced')}"
        )
    return 0 if ok_a else 1


def gh_json(args: list[str]) -> dict | None:
    try:
        out = subprocess.run(
            ["gh", *args], capture_output=True, text=True, timeout=30, check=True
        ).stdout
        return json.loads(out) if out.strip() else {}
    except (subprocess.SubprocessError, OSError, json.JSONDecodeError):
        return None


def cmd_github(args: argparse.Namespace) -> int:
    if resolve(MAIN, "A") != sorted(PAGES_A):
        print(
            f"❌ {MAIN} todavía no resuelve a GitHub Pages. "
            "Revisa `status` y espera la propagación."
        )
        return 1
    pages = gh_json(["api", f"repos/{REPO}/pages"]) or {}
    if pages.get("cname") != MAIN:
        if gh_json(["api", "-X", "PUT", f"repos/{REPO}/pages", "-f", f"cname={MAIN}"]) is None:
            print("❌ No se pudo configurar el dominio en Pages (¿gh autenticado como owner?).")
            return 1
        print(f"✓ Dominio {MAIN} configurado en Pages")
    deadline = time.time() + args.wait * 60
    while True:
        pages = gh_json(["api", f"repos/{REPO}/pages"]) or {}
        state = (pages.get("https_certificate") or {}).get("state")
        print(f"  certificado: {state or 'pendiente'}")
        if state == "approved":
            break
        if time.time() > deadline:
            print("⏳ El certificado aún no está listo. Vuelve a ejecutar `github` más tarde.")
            return 1
        time.sleep(30)
    if not pages.get("https_enforced"):
        gh_json(["api", "-X", "PUT", f"repos/{REPO}/pages", "-F", "https_enforced=true"])
        print("✓ HTTPS forzado")
    print(f"✅ https://{MAIN} listo")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("plan", "apply"):
        p = sub.add_parser(name)
        p.add_argument("--github-txt", help=f"valor del TXT {GITHUB_TXT_NAME} que entrega GitHub")
        p.add_argument(
            "--prune", action="store_true", help="borra A/AAAA/CNAME que sobran en @ y www"
        )
    s = sub.add_parser("status")
    s.add_argument(
        "--activation-check", action="store_true", help="pide a Cloudflare revisar los NS"
    )
    g = sub.add_parser("github")
    g.add_argument("--wait", type=int, default=20, help="minutos máximos esperando el certificado")
    args = ap.parse_args(argv)
    try:
        if args.cmd in ("plan", "apply"):
            return cmd_plan_apply(args, apply=args.cmd == "apply")
        if args.cmd == "status":
            return cmd_status(args)
        return cmd_github(args)
    except CloudflareError as exc:
        print(f"❌ Cloudflare: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
