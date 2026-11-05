import json

import check_ready as cr

READY = """### Contexto
Los enlaces compartidos se ven sin imagen.

### Objetivo
Cada post tiene su imagen Open Graph.

### Alcance
- Generar imágenes al compilar

### Fuera de alcance
- Imágenes del radar

### Criterios de aceptación
- [ ] Imagen 1200×630 por post
- [ ] `npm run build` pasa

### Cómo verificar
`npm run build` y revisar `dist/og/`.

### Pistas técnicas
`src/layouts/BaseLayout.astro`

### Dependencias
Ninguna.
"""


def test_issue_completo_esta_ready():
    assert cr.check(READY, ["web"]) == []


def test_alias_de_titulos_y_nivel_2():
    body = READY.replace("### Contexto", "## Por qué").replace("### Objetivo", "## Qué")
    assert cr.check(body, ["web"]) == []


def test_faltan_secciones():
    problems = cr.check("### Contexto\nAlgo\n", ["web"])
    assert any("Objetivo" in p for p in problems)
    assert any("Criterios de aceptación" in p for p in problems)
    assert len(problems) == 7


def test_seccion_vacia_de_issue_form():
    body = READY.replace("Ninguna.", "_No response_")
    assert cr.check(body, ["web"]) == ["La sección «Dependencias» está vacía."]


def test_criterios_sin_casillas():
    body = READY.replace(
        "- [ ] Imagen 1200×630 por post\n- [ ] `npm run build` pasa", "Que funcione bien."
    )
    assert any("casillas" in p for p in cr.check(body, ["web"]))


def test_decisiones_abiertas():
    body = READY + "\n### Decisiones abiertas\n- ¿Qué librería usamos?\n- ~~¿Formato PNG?~~ PNG\n"
    problems = cr.check(body, ["web"])
    assert len(problems) == 1 and "¿Qué librería usamos?" in problems[0]
    resolved = READY + "\n### Decisiones abiertas\n- [x] ¿Qué librería usamos? satori\n"
    assert cr.check(resolved, ["web"]) == []
    assert cr.check(READY + "\n## Decisiones abiertas\nNinguna\n", ["web"]) == []
    assert (
        cr.check(READY + "\n## Decisiones abiertas\nNinguna: este issue decide.\n", ["web"]) == []
    )


def test_labels():
    assert any("área" in p for p in cr.check(READY, []))
    assert any("idea" in p for p in cr.check(READY, ["web", "idea"]))


def test_issue_refs():
    assert cr.issue_refs(
        "implementa el #12 y el issue 30, mira https://github.com/o/r/issues/7"
    ) == [12, 30, 7]
    assert cr.issue_refs("color #FFF y paso 3") == []
    assert cr.issue_refs("#1 #2 #3 #4") == [1, 2, 3]


def test_event_y_json(tmp_path, capsys):
    ev = tmp_path / "ev.json"
    ev.write_text(
        json.dumps(
            {"issue": {"number": 5, "title": "T", "body": READY, "labels": [{"name": "web"}]}}
        )
    )
    assert cr.main(["--event", str(ev), "--json"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"number": 5, "ready": True, "has_ready_label": False, "problems": []}


def test_hook_avisa_issue_incompleto(monkeypatch, capsys):
    monkeypatch.setattr(
        cr,
        "fetch_issue",
        lambda n, repo=None: {"number": n, "title": "X", "state": "open", "body": "", "labels": []},
    )
    assert cr.hook(json.dumps({"prompt": "implementa el #9"})) == 0
    out = json.loads(capsys.readouterr().out)
    assert "#9" in out["systemMessage"]
    assert "NO cumple" in out["hookSpecificOutput"]["additionalContext"]


def test_hook_silencioso_si_esta_ready(monkeypatch, capsys):
    data = {
        "number": 4,
        "title": "X",
        "state": "open",
        "body": READY,
        "labels": [{"name": "web"}, {"name": "ready"}],
    }
    monkeypatch.setattr(cr, "fetch_issue", lambda n, repo=None: data)
    assert cr.hook(json.dumps({"prompt": "toma el #4"})) == 0
    assert capsys.readouterr().out == ""


def test_hook_ignora_prompts_sin_issues(capsys):
    assert cr.hook(json.dumps({"prompt": "hola"})) == 0
    assert capsys.readouterr().out == ""
