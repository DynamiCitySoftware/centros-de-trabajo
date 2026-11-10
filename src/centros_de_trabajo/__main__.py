import sys

from PyQt6.QtWidgets import QApplication

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.config import Config
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.ui.interfaz_principal import InterfazVenta


def crear_backend(config: Config) -> Backend:
    """Construye el backend seleccionado, sin acoplarlo a la UI."""
    if config.backend == "fake":
        # Datos ficticios para desarrollar y probar la interfaz.
        ordenes_demo = [
            OrdenDeTrabajo(
                id=1001,
                nombre="Torneado de prueba (fake)",
                state="ready",
                is_user_working=False,
                working_state="normal",
            ),
            OrdenDeTrabajo(
                id=1002,
                nombre="Ensamblaje de prueba (fake)",
                state="ready",
                is_user_working=False,
                working_state="normal",
            ),
        ]
        return FakeBackend(ordenes_demo)

    if config.backend == "odoo":
        return OdooBackend(
            config.odoo_url,
            config.odoo_db,
            config.odoo_user,
            config.odoo_key_file,
        )

    raise ValueError(f"Backend desconocido: {config.backend!r}")


def main() -> int:
    try:
        config = Config.desde_entorno()
        backend = crear_backend(config)
    except (OSError, ValueError) as error:
        print(f"Error de configuración: {error}", file=sys.stderr)
        return 2

    app = QApplication(sys.argv)
    app.setApplicationName("centros_de_trabajo")

    ventana = InterfazVenta(backend)

    if config.kiosco:
        ventana.showFullScreen()
    else:
        ventana.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())