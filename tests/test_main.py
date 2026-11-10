from pathlib import Path

from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.config import Config
from centros_de_trabajo.__main__ import crear_backend


def test_composicion_crea_fake_y_dos_ordenes_demo():
    config = Config(
        backend="fake",
        kiosco=False,
        odoo_url="",
        odoo_db="",
        odoo_user="",
        odoo_key_file=Path("/no-se-usa"),
    )

    backend = crear_backend(config)

    assert isinstance(backend, FakeBackend)
    assert [orden.id for orden in backend.listar_ordenes()] == [1001, 1002]