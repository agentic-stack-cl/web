import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"
FIXTURE = FIXTURES / "forum.json"


@pytest.fixture
def radar_data():
    """Copia fija del radar: los tests no deben depender de lo que se vote en el foro."""
    return json.loads((FIXTURES / "radar-base.json").read_text(encoding="utf-8"))


@pytest.fixture
def repo_radar():
    """El radar real del repo, solo para validar su contenido."""
    return json.loads((ROOT / "src" / "data" / "radar.json").read_text(encoding="utf-8"))


@pytest.fixture
def fixture_path():
    return FIXTURE
