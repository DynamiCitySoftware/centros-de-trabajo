# Ruta: src/centros_de_trabajo/ui/seleccion_centro.py en PC LAB
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.base import CentroDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno


def construir_registro_centros() -> list[CentroDeTrabajo]:
    return [CentroHorno()]


def filtrar_ordenes_por_centro(
    centro_seleccionado: CentroDeTrabajo,
    todas_las_ordenes: list[OrdenDeTrabajo],
) -> list[OrdenDeTrabajo]:
    return [ot for ot in todas_las_ordenes if centro_seleccionado.es_mia(ot)]


def elegir_centro_por_nombre(
    nombre_odoo_buscado: str,
    registro_centros: list[CentroDeTrabajo],
) -> CentroDeTrabajo:
    for centro in registro_centros:
        if centro.nombre_odoo == nombre_odoo_buscado:
            return centro
    raise ValueError(f"No hay centro registrado con nombre_odoo={nombre_odoo_buscado!r}")


def contar_por_centro(
    registro_centros: list[CentroDeTrabajo],
    todas_las_ordenes: list[OrdenDeTrabajo],
) -> dict[str, int]:
    return {
        centro.nombre_odoo: len(filtrar_ordenes_por_centro(centro, todas_las_ordenes))
        for centro in registro_centros
    }


class VentanaSeleccion(QMainWindow):
    def __init__(self, backend_a_usar: Backend, registro_centros: list[CentroDeTrabajo]) -> None:
        super().__init__()
        self._backend = backend_a_usar
        self._registro = registro_centros
        self.centro_elegido: CentroDeTrabajo | None = None
        self.setWindowTitle("Kiosco Tornería - Elegir centro")
        self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()
        self._etiqueta = QLabel("Elegí centro de trabajo")
        self._lista = QListWidget()
        self._boton_abrir = QPushButton("ABRIR CENTRO [F1]")
        layout.addWidget(self._etiqueta)
        layout.addWidget(self._lista)
        layout.addWidget(self._boton_abrir)
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)
        self._boton_abrir.clicked.connect(self._al_abrir)
        self.recargar()

    def recargar(self) -> None:
        print("[seleccion] recargar inicio", flush=True)
        todas = self._backend.listar_ordenes()
        conteos = contar_por_centro(self._registro, todas)
        self._lista.clear()
        for centro in self._registro:
            n = conteos.get(centro.nombre_odoo, 0)
            self._lista.addItem(f"{centro.nombre_odoo} — {n} órdenes")
        print(f"[seleccion] conteos={conteos}", flush=True)

    def _al_abrir(self) -> None:
        fila = self._lista.currentRow()
        if fila < 0 or fila >= len(self._registro):
            self._etiqueta.setText("Elegí un centro primero")
            return
        self.centro_elegido = self._registro[fila]
        print(f"[seleccion] elegido={self.centro_elegido.nombre_odoo}", flush=True)
        self.close()