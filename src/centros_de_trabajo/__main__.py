# Ruta: src/centros_de_trabajo/__main__.py en PC LAB
import sys
from PyQt6.QtWidgets import QApplication

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.config import Config
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno
from centros_de_trabajo.politicas_ct.horno.mock_horno import MockHorno
from centros_de_trabajo.ui.seleccion_centro import construir_registro_centros, VentanaSeleccion
from centros_de_trabajo.ui.ui_horno import VentanaHorno


def construir_backend_desde_config(config: Config) -> Backend:
    if config.backend == "odoo":
        return OdooBackend(url=config.odoo_url, db=config.odoo_db, user=config.odoo_user, key_file=config.odoo_key_file)
    return FakeBackend([
        OrdenDeTrabajo(id_odoo=41, operacion_nombre="horneado budin", estado_odoo="ready", workcenter_nombre="Horno Microondas", usuario_es_responsable=False, existe_cronometro_para_usuario=False, duracion_minutos=0.0),
        OrdenDeTrabajo(id_odoo=42, operacion_nombre="horneado simple", estado_odoo="ready", workcenter_nombre="Horno Microondas", usuario_es_responsable=False, existe_cronometro_para_usuario=False, duracion_minutos=0.0),
    ])


def main() -> None:
    config = Config.desde_entorno()
    backend_a_usar = construir_backend_desde_config(config)
    registro = construir_registro_centros()
    app = QApplication(sys.argv)

    seleccion = VentanaSeleccion(backend_a_usar, registro)
    if not config.kiosco:
        seleccion.showNormal()

    # Cuando se cierra con centro elegido, abrimos su UI.
    from PyQt6.QtCore import QTimer
    ventana_horno: list = []

    def abrir_si_hay_eleccion() -> None:
        if seleccion.centro_elegido is None:
            return
        centro = seleccion.centro_elegido
        if isinstance(centro, CentroHorno):
            v = VentanaHorno(backend_a_usar, centro, MockHorno())
            if not config.kiosco:
                v.showNormal()
            ventana_horno.append(v)

    seleccion._boton_abrir.clicked.connect(lambda: QTimer.singleShot(100, abrir_si_hay_eleccion))
    sys.exit(app.exec())


if __name__ == "__main__":
    main()