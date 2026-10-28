import pytest

from centros_de_trabajo.config import Config


def test_por_defecto_es_fake(monkeypatch):
    monkeypatch.delenv("BACKEND", raising=False)
    assert Config.desde_entorno().backend == "fake"


def test_odoo_sin_variables_falla(monkeypatch):
    monkeypatch.setenv("BACKEND", "odoo")
    for var in ("ODOO_URL", "ODOO_DB", "ODOO_USER"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(ValueError, match="ODOO_URL"):
        Config.desde_entorno()