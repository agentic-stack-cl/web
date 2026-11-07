import copy

import radar


def test_radar_json_del_repo_es_valido(repo_radar):
    assert radar.validate(repo_radar) == []


def test_slugify():
    assert radar.slugify("Model Context Protocol (MCP)") == "model-context-protocol-mcp"
    assert radar.slugify("Técnicas y diseño ñandú") == "tecnicas-y-diseno-nandu"


def test_validate_detecta_errores(radar_data):
    bad = copy.deepcopy(radar_data)
    e = bad["entries"][0]
    e["ring"] = "quizas"
    e["moved"] = 5
    e["description"] = "x" * 300
    bad["entries"].append(copy.deepcopy(bad["entries"][1]))  # id duplicado
    errors = "\n".join(radar.validate(bad))
    assert "'ring'" in errors
    assert "'moved'" in errors
    assert "280" in errors
    assert "duplicado" in errors


def test_votado_requiere_hilo(radar_data):
    bad = copy.deepcopy(radar_data)
    bad["entries"][0]["status"] = "votado"
    assert any("threadId" in err for err in radar.validate(bad))


def test_diff_y_formato_discord(radar_data):
    new = copy.deepcopy(radar_data)
    new["entries"][0]["ring"] = "probar"
    new["entries"].append({**new["entries"][1], "id": "nuevo", "name": "Nuevo blip"})
    changes = radar.diff(radar_data, new)
    assert [e["id"] for e in changes["added"]] == ["nuevo"]
    assert changes["moved"][0]["from"] == "adoptar"
    msg = radar.format_discord(changes, heading="Prueba")
    assert "🆕" in msg and "↕️" in msg and len(msg) <= 1800


def test_formato_discord_respeta_limite(radar_data):
    many = {"added": [radar_data["entries"][0]] * 200, "moved": [], "removed": [], "updated": []}
    assert len(radar.format_discord(many, heading="Mucho")) <= 1800
