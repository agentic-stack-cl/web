import setup as dns


def test_registros_del_dominio_principal():
    recs = dns.desired_records(dns.MAIN)
    assert sum(r.type == "A" for r in recs) == 4
    assert sum(r.type == "AAAA" for r in recs) == 4
    assert dns.Record("CNAME", "www", "agentic-stack-cl.github.io") in recs
    assert not any(r.proxied for r in recs)  # GitHub necesita DNS only para emitir el certificado
    txt = dns.desired_records(dns.MAIN, "abc123")[-1]
    assert txt.fqdn(dns.MAIN) == "_github-pages-challenge-agentic-stack-cl.agenticstack.cl"


def test_registros_del_alias_van_proxied():
    recs = dns.desired_records(dns.ALIAS)
    assert {r.fqdn(dns.ALIAS) for r in recs} == {"theagenticstack.cl", "www.theagenticstack.cl"}
    assert all(r.proxied for r in recs)


def existing(type_, name, content, proxied=False, id_="x"):
    return {"id": id_, "type": type_, "name": name, "content": content, "proxied": proxied}


def test_plan_idempotente_y_conflictos():
    zone = dns.MAIN
    wanted = dns.desired_records(zone, "tok")
    have = [
        existing(r.type, r.fqdn(zone), r.content if r.type != "TXT" else '"tok"') for r in wanted
    ]
    plan = dns.plan_records(zone, have, wanted)
    assert plan.create == [] and plan.fix_proxy == [] and plan.conflicts == []

    have.append(existing("A", "agenticstack.cl", "1.2.3.4", id_="viejo"))
    have.append(existing("MX", "agenticstack.cl", "mail.example.com", id_="mx"))
    plan = dns.plan_records(zone, have, wanted)
    assert [c["id"] for c in plan.conflicts] == ["viejo"]  # el MX no se toca


def test_plan_corrige_proxy():
    zone = dns.ALIAS
    wanted = dns.desired_records(zone)
    have = [existing("A", "theagenticstack.cl", dns.PLACEHOLDER_IP, proxied=False, id_="a")]
    plan = dns.plan_records(zone, have, wanted)
    assert len(plan.create) == 1 and plan.fix_proxy[0][0]["id"] == "a"


def test_regla_de_redireccion():
    rule = dns.redirect_rule()
    target = rule["action_parameters"]["from_value"]
    assert target["status_code"] == 301 and target["preserve_query_string"] is True
    assert "https://agenticstack.cl" in target["target_url"]["expression"]
    assert "www.theagenticstack.cl" in rule["expression"]


class FakeCF(dns.Cloudflare):
    def __init__(self):
        super().__init__("token")
        self.calls = []

    def request(self, method, path, body=None, query=None):
        self.calls.append((method, path, body))
        return {}


def test_put_redirect_conserva_otras_reglas_y_reemplaza_la_propia():
    cf = FakeCF()
    existing_rs = {
        "id": "rs1",
        "rules": [
            {"id": "1", "version": "3", "ref": "otra", "expression": "true", "action": "redirect"},
            {"id": "2", "ref": dns.REDIRECT_REF, "expression": "viejo", "action": "redirect"},
        ],
    }
    cf.put_redirect("z1", existing_rs)
    method, path, body = cf.calls[-1]
    assert (method, path) == ("PUT", "/zones/z1/rulesets/rs1")
    refs = [r["ref"] for r in body["rules"]]
    assert refs == ["otra", dns.REDIRECT_REF]
    assert "id" not in body["rules"][0] and "version" not in body["rules"][0]


def test_put_redirect_crea_ruleset_si_no_existe():
    cf = FakeCF()
    cf.put_redirect("z1", None)
    method, path, body = cf.calls[-1]
    assert (method, path) == ("POST", "/zones/z1/rulesets")
    assert body["phase"] == "http_request_dynamic_redirect"


def test_sin_token_termina_con_mensaje(monkeypatch):
    monkeypatch.delenv("CLOUDFLARE_API_TOKEN", raising=False)
    try:
        dns.main(["plan"])
    except SystemExit as exc:
        assert "CLOUDFLARE_API_TOKEN" in str(exc.code)
    else:
        raise AssertionError("debió terminar")


class RoutedCF(dns.Cloudflare):
    """Cloudflare falso con zonas existentes: registra las rutas pedidas."""

    def __init__(self):
        super().__init__("token")
        self.paths = []

    def request(self, method, path, body=None, query=None):
        self.paths.append((method, path))
        if path == "/accounts":
            raise AssertionError("no debería pedir la cuenta si las zonas existen")
        if path == "/zones":
            return [{"id": query["name"], "status": "active", "name_servers": ["a.ns", "b.ns"]}]
        if path.endswith("/dns_records"):
            return []
        if path.endswith("/entrypoint"):
            return None
        return {}


def test_plan_con_zonas_existentes_no_requiere_permiso_de_cuenta(monkeypatch, capsys):
    cf = RoutedCF()
    monkeypatch.setattr(dns, "client", lambda: cf)
    monkeypatch.setattr(dns, "resolve", lambda name, rtype: [])
    args = dns.argparse.Namespace(github_txt="tok", prune=False)
    assert dns.cmd_plan_apply(args, apply=False) == 0
    assert all(m == "GET" for m, _ in cf.paths)
    assert "+ A" in capsys.readouterr().out
