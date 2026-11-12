# Ruta: src/centros_de_trabajo/__main__.py en PC LAB - reemplazar TODO el archivo
import sys

from PyQt6.QtWidgets import QApplication

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.config import Config
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno
from centros_de_trabajo.politicas_ct.horno.mock_horno import MockHorno
from centros_de_trabajo.ui.seleccion_centro import (
    construir_registro_centros,
    elegir_centro_por_nombre,
)
from centros_de_trabajo.ui.ui_horno import VentanaHorno


def construir_backend_desde_config(config: Config) -> Backend:
    if config.backend == "odoo":
        return OdooBackend(
            url=config.odoo_url,
            db=config.odoo_db,
            user=config.odoo_user,
            key_file=config.odoo_key_file,
        )
    # Fake con 2 WOs de horno para probar la UI sin red.
    ordenes_demo = [
        OrdenDeTrabajo(
            id_odoo=34,
            operacion_nombre="horneado simple",
            estado_odoo="ready",
            workcenter_nombre="Horno Microondas",
            usuario_es_responsable=False,
            existe_cronometro_para_usuario=False,
            duracion_minutos=0.0,
        ),
        OrdenDeTrabajo(
            id_odoo=38,
            operacion_nombre="horneado simple",
            estado_odoo="ready",
            workcenter_nombre="Horno Microondas",
            usuario_es_responsable=False,
            existe_cronometro_para_usuario=False,
            duracion_minutos=0.0,
        ),
    ]
    return FakeBackend(ordenes_demo)


def main() -> None:
    config = Config.desde_entorno()
    backend_a_usar = construir_backend_desde_config(config)
    registro_centros = construir_registro_centros()
    centro_horno = elegir_centro_por_nombre("Horno Microondas", registro_centros)
    assert isinstance(centro_horno, CentroHorno)
    horno_fisico_o_mock = MockHorno()

    app = QApplication(sys.argv)
    ventana = VentanaHorno(backend_a_usar, centro_horno, horno_fisico_o_mock)
    # VentanaHorno hace showFullScreen en __init__.
    # Si KIOSCO=0 la bajamos a ventana normal para desarrollar en PC LAB.
    if not config.kiosco:
        ventana.showNormal()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()