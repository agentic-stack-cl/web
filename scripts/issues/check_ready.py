#!/usr/bin/env python3
"""Valida si un issue cumple la Definition of Ready (docs/ISSUES.md).

Fuente única de las reglas: la usan la plantilla de issue (por sus títulos), el hook
UserPromptSubmit de Claude Code, la skill /issue-ready, /implement-issue y el workflow
.github/workflows/issue-ready.yml.

Uso:
  python3 scripts/issues/check_ready.py --issue 42          # consulta GitHub con gh
  python3 scripts/issues/check_ready.py --body-file issue.md --labels web
  python3 scripts/issues/check_ready.py --event "$GITHUB_EVENT_PATH"   # en Actions
  python3 scripts/issues/check_ready.py --hook < prompt.json           # hook de Claude Code

Código de salida: 0 ready · 1 incompleto · 2 error de uso o de red.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

READY_LABEL = "ready"
IDEA_LABEL = "idea"
AREA_LABELS = ("web", "radar", "post", "infra", "agentic")
DOC = "docs/ISSUES.md"

# Secciones obligatorias: clave → (título canónico, alias aceptados normalizados)
SECTIONS: dict[str, tuple[str, tuple[str, ...]]] = {
    "contexto": ("Contexto", ("contexto", "por que", "problema")),
    "objetivo": ("Objetivo", ("objetivo", "que", "resultado esperado")),
    "alcance": ("Alcance", ("alcance", "alcance propuesto", "incluye")),
    "fuera": ("Fuera de alcance", ("fuera de alcance", "no incluye")),
    "criterios": ("Criterios de aceptación", ("criterios de aceptacion",)),
    "verificar": ("Cómo verificar", ("como verificar", "verificacion", "como probar")),
    "pistas": ("Pistas técnicas", ("pistas tecnicas", "notas tecnicas", "archivos")),
    "dependencias": ("Dependencias", ("dependencias", "bloqueos", "dependencias y bloqueos")),
}
OPEN_DECISIONS = ("decisiones abiertas", "preguntas abiertas")
EMPTY_MARKERS = {"", "_no response_", "no response", "todo", "tbd", "pendiente", "..."}
NONE_MARKERS = {"ninguna", "ninguno", "no hay", "sin decisiones abiertas", "n/a"}

_HEADING = re.compile(r"^(#{2,3})\s+(.+?)\s*#*\s*$")
_CHECKBOX = re.compile(r"^\s*[-*]\s+\[[ xX]\]\s+\S")
_ISSUE_REF = re.compile(
    r"(?:(?<![\w/])#(\d{1,6})\b|\b(?:issue|ticket|tarea)\s+#?(\d{1,6})\b|/issues/(\d{1,6})\b)",
    re.IGNORECASE,
)


def norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", text).strip()


def split_sections(body: str) -> dict[str, str]:
    """{título normalizado: contenido} para encabezados ## y ###."""
    sections: dict[str, list[str]] = {}
    current: str | None = None
    for line in (body or "").replace("\r\n", "\n").split("\n"):
        m = _HEADING.match(line)
        if m:
            current = norm(m.group(2))
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
    return {k: "\n".join(v).strip() for k, v in sections.items()}


def is_empty(content: str) -> bool:
    text = re.sub(r"<!--.*?-->", "", content, flags=re.S).strip()
    return norm(text) in {norm(m) for m in EMPTY_MARKERS}


def says_none(text: str) -> bool:
    """«Ninguna», «Ninguna: este issue decide…», «No hay.» cuentan como sin decisiones."""
    t = norm(text)
    return any(t == m or t.startswith(m + " ") for m in (norm(x) for x in NONE_MARKERS))


def unresolved_decisions(content: str) -> list[str]:
    """Decisiones sin resolver. Resueltas: `- [x] ...`, `- ~~...~~` o «Ninguna»."""
    items: list[str] = []
    saw_list = False
    for line in content.split("\n"):
        m = re.match(r"^\s*[-*]\s+(\[[ xX]\]\s+)?(.*)$", line)
        if not m:
            continue
        saw_list = True
        checked = bool(m.group(1)) and "x" in m.group(1).lower()
        text = m.group(2).strip()
        if checked or text.startswith("~~") or says_none(text) or not text:
            continue
        items.append(text)
    if not saw_list and not is_empty(content) and not says_none(content):
        items.append(content.strip().split("\n")[0])
    return items


@dataclass
class Report:
    number: int | None = None
    title: str = ""
    labels: list[str] = field(default_factory=list)
    problems: list[str] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not self.problems

    @property
    def has_ready_label(self) -> bool:
        return READY_LABEL in self.labels


def check(body: str, labels: list[str] | None = None) -> list[str]:
    """Lista de problemas (vacía si el issue cumple la Definition of Ready)."""
    labels = [label.lower() for label in (labels or [])]
    problems: list[str] = []
    sections = split_sections(body)

    for key, (title, aliases) in SECTIONS.items():
        content = next((sections[a] for a in aliases if a in sections), None)
        if content is None:
            problems.append(f"Falta la sección «{title}».")
        elif is_empty(content):
            problems.append(f"La sección «{title}» está vacía.")
        elif key == "criterios":
            boxes = [ln for ln in content.split("\n") if _CHECKBOX.match(ln)]
            if not boxes:
                problems.append(
                    "«Criterios de aceptación» debe ser una lista de casillas `- [ ] ...`."
                )

    for alias in OPEN_DECISIONS:
        if alias in sections:
            pending = unresolved_decisions(sections[alias])
            if pending:
                problems.append(
                    f"Hay {len(pending)} decisión(es) abierta(s) sin resolver: «{pending[0]}»"
                    + (" y otras." if len(pending) > 1 else ".")
                )

    if IDEA_LABEL in labels:
        problems.append(f"Tiene el label `{IDEA_LABEL}`: primero debe aceptarse y pasar a Backlog.")
    if not any(a in labels for a in AREA_LABELS):
        problems.append(f"Falta un label de área ({', '.join(AREA_LABELS)}).")
    return problems


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------


def repo_slug() -> str | None:
    try:
        url = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        ).stdout.strip()
    except (subprocess.SubprocessError, OSError):
        return None
    m = re.search(r"github\.com[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
    return m.group(1) if m else None


def fetch_issue(number: int, repo: str | None = None) -> dict | None:
    """Issue vía `gh api`. None si es un PR, no existe o no hay gh."""
    repo = repo or repo_slug()
    if not repo:
        return None
    try:
        out = subprocess.run(
            ["gh", "api", f"repos/{repo}/issues/{number}"],
            capture_output=True,
            text=True,
            timeout=10,
            check=True,
        ).stdout
    except (subprocess.SubprocessError, OSError):
        return None
    data = json.loads(out)
    return None if "pull_request" in data else data


def report_from_issue(data: dict) -> Report:
    labels = [lb["name"] if isinstance(lb, dict) else lb for lb in data.get("labels", [])]
    return Report(
        number=data.get("number"),
        title=data.get("title", ""),
        labels=labels,
        problems=check(data.get("body") or "", labels),
    )


def issue_refs(prompt: str, limit: int = 3) -> list[int]:
    seen: list[int] = []
    for m in _ISSUE_REF.finditer(prompt or ""):
        n = int(next(g for g in m.groups() if g))
        if n not in seen:
            seen.append(n)
    return seen[:limit]


def format_report(r: Report) -> str:
    head = f"#{r.number} «{r.title}»" if r.number else "El issue"
    if r.ready:
        tail = "" if r.has_ready_label else f" (falta poner el label `{READY_LABEL}`)"
        return f"✅ {head} cumple la Definition of Ready{tail}."
    lines = [f"⚠️ {head} NO cumple la Definition of Ready ({DOC}):"]
    lines += [f"  - {p}" for p in r.problems]
    return "\n".join(lines)


def hook(stdin: str) -> int:
    """Hook UserPromptSubmit: avisa si el prompt menciona issues incompletos. Nunca bloquea."""
    try:
        prompt = json.loads(stdin or "{}").get("prompt", "")
    except json.JSONDecodeError:
        return 0
    reports = []
    for n in issue_refs(prompt):
        data = fetch_issue(n)
        if data and data.get("state") == "open":
            reports.append(report_from_issue(data))
    pending = [r for r in reports if not r.ready or not r.has_ready_label]
    if not pending:
        return 0
    context = "\n".join(format_report(r) for r in pending) + (
        "\n\nRegla del repo (CLAUDE.md): no implementes un issue que no cumpla la Definition "
        f"of Ready o no tenga el label `{READY_LABEL}`. Explica qué falta y ofrece "
        "completarlo con la skill /issue-ready antes de escribir código."
    )
    nums = ", ".join(f"#{r.number}" for r in pending)
    out = {
        "systemMessage": f"Issue {nums} sin Definition of Ready completa (ver {DOC}).",
        "hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": context},
    }
    print(json.dumps(out, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--issue", type=int, help="número de issue (usa gh)")
    src.add_argument("--body-file", help="archivo con el cuerpo del issue en Markdown")
    src.add_argument("--event", help="payload de un evento `issues` de GitHub Actions")
    src.add_argument("--hook", action="store_true", help="modo hook UserPromptSubmit (lee stdin)")
    ap.add_argument("--labels", default="", help="labels separados por coma (con --body-file)")
    ap.add_argument("--repo", help="owner/repo (por defecto, el remoto origin)")
    ap.add_argument("--json", action="store_true", help="salida en JSON")
    args = ap.parse_args(argv)

    if args.hook:
        return hook(sys.stdin.read())

    if args.issue:
        data = fetch_issue(args.issue, args.repo)
        if data is None:
            print(
                f"No se pudo leer el issue #{args.issue} (¿es un PR?, ¿gh autenticado?)",
                file=sys.stderr,
            )
            return 2
        report = report_from_issue(data)
    elif args.event:
        report = report_from_issue(
            json.loads(Path(args.event).read_text(encoding="utf-8"))["issue"]
        )
    else:
        labels = [x.strip() for x in args.labels.split(",") if x.strip()]
        report = Report(
            labels=labels, problems=check(Path(args.body_file).read_text(encoding="utf-8"), labels)
        )

    if args.json:
        print(
            json.dumps(
                {
                    "number": report.number,
                    "ready": report.ready,
                    "has_ready_label": report.has_ready_label,
                    "problems": report.problems,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(format_report(report))
    return 0 if report.ready else 1


if __name__ == "__main__":
    sys.exit(main())
