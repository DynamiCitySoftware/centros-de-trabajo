from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.estado import derivar_estado, ordenes_validas
from centros_de_trabajo.core.ordenes import Orden


class InterfazVenta(QMainWindow):
    ACCIONES = (
        (Orden.INICIAR, "Iniciar proceso", "F1"),
        (Orden.PAUSAR, "Pausar proceso", "F2"),
        (Orden.REANUDAR, "Reanudar proceso", "F3"),
        (Orden.TERMINAR, "Finalizar proceso", "F4"),
    )

    def __init__(self, backend: Backend) -> None:
        super().__init__()
        # refresco automatico
        self._timer = QTimer(self)
        self._timer.setInterval(10000)
        self._timer.timeout.connect(lambda: self.refrescar_ordenes())
        self._timer.start()

        self.backend = backend
        self._ordenes_por_id = {}
        self._listado_disponible = False

        self.setWindowTitle("KIOSCO Torneria - Prototipo UI")
        self.setMinimumSize(800, 500)

        container = QWidget()
        layout = QVBoxLayout(container)

        self.lista_ordenes = QListWidget()
        self.lista_ordenes.setObjectName("lista_ordenes")
        self.lista_ordenes.currentItemChanged.connect(self._seleccion_cambiada)
        layout.addWidget(self.lista_ordenes)

        self.detalle = QLabel("Seleccioná una orden de trabajo.")
        self.detalle.setObjectName("detalle_orden")
        self.detalle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.detalle)

        self.mensaje = QLabel("")
        self.mensaje.setObjectName("mensaje")
        layout.addWidget(self.mensaje)

        fila_botones = QHBoxLayout()
        self.botones: dict[Orden, QPushButton] = {}

        for orden, texto, tecla in self.ACCIONES:
            boton = QPushButton(f"{texto}\n[{tecla}]")
            boton.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
            boton.setMinimumWidth(0) 
            boton.setObjectName(f"btn_{orden.value}")
            boton.setStyleSheet(self.get_style("#3498db"))
            boton.clicked.connect(
                lambda checked=False, accion=orden: self._ejecutar_orden(accion)
            )
            self.botones[orden] = boton
            fila_botones.addWidget(boton)

            atajo = QShortcut(QKeySequence(tecla), self)
            atajo.activated.connect(
                lambda accion=orden: self._ejecutar_orden(accion)
            )

        layout.addLayout(fila_botones)
        self.setCentralWidget(container)

        # Atajo de salida para desarrollador: Ctrl+Alt+S
        exit_sc = QShortcut(QKeySequence("Ctrl+Alt+S"), self)
        exit_sc.activated.connect(self.close)

        self.refrescar_ordenes()

        

    @staticmethod
    def get_style(color: str) -> str:
        """Genera el estilo visual de los botones."""
        return f"""
            QPushButton {{
                font-size: 18px;
                font-weight: bold;
                background-color: {color};
                color: white;
                border-radius: 16px;
                margin: 4px;
                border: 4px solid #2980b9;
                padding: 8px;
                min-width: 0px;
            }}
        """

    def refrescar_ordenes(self, mensaje: str | None = None) -> None:
        """Vuelve a leer el backend y conserva la selección cuando puede."""
        item_actual = self.lista_ordenes.currentItem()
        id_seleccionado = (
            item_actual.data(Qt.ItemDataRole.UserRole)
            if item_actual is not None
            else None
        )

        try:
            ordenes = self.backend.listar_ordenes()
        except Exception as error:
            self._listado_disponible = False
            self.mensaje.setText(f"No se pudo cargar el listado: {error}")
            for boton in self.botones.values():
                boton.setEnabled(False)
            return

        self._listado_disponible = True
        self._ordenes_por_id = {orden.id: orden for orden in ordenes}
        self.lista_ordenes.clear()

        item_seleccionado = None

        for orden in ordenes:
            estado = derivar_estado(orden)
            item = QListWidgetItem(
                f"WO {orden.id} — {orden.nombre} — {estado.value}"
            )
            item.setData(Qt.ItemDataRole.UserRole, orden.id)
            self.lista_ordenes.addItem(item)

            if orden.id == id_seleccionado:
                item_seleccionado = item

        if item_seleccionado is None and self.lista_ordenes.count():
            item_seleccionado = self.lista_ordenes.item(0)

        self.lista_ordenes.setCurrentItem(item_seleccionado)

        if mensaje is not None:
            self.mensaje.setText(mensaje)
        else:
            self.mensaje.setText(f"{len(ordenes)} órdenes cargadas.")

        if item_seleccionado is None:
            self.detalle.setText("No hay órdenes para mostrar.")
            for boton in self.botones.values():
                boton.setEnabled(False)

    def _seleccion_cambiada(self, actual, anterior=None) -> None:
        if actual is None:
            self.detalle.setText("Seleccioná una orden de trabajo.")
            for boton in self.botones.values():
                boton.setEnabled(False)
            return

        id_orden = actual.data(Qt.ItemDataRole.UserRole)
        orden = self._ordenes_por_id.get(id_orden)

        if orden is None:
            self.detalle.setText("No se pudo cargar el detalle de la orden.")
            for boton in self.botones.values():
                boton.setEnabled(False)
            return

        estado = derivar_estado(orden)
        self.detalle.setText(
            f"WO {orden.id} — {orden.nombre}\n"
            f"Estado Odoo: {orden.state} | Estado kiosco: {estado.value}"
        )

        validas = ordenes_validas(estado)
        for accion, boton in self.botones.items():
            boton.setEnabled(self._listado_disponible and accion in validas)

    def _ejecutar_orden(self, accion: Orden) -> None:
        if not self._listado_disponible:
            return

        item = self.lista_ordenes.currentItem()
        if item is None:
            return

        id_orden = item.data(Qt.ItemDataRole.UserRole)

        try:
            resultado = self.backend.enviar(accion, id_orden)
            print(f"[kiosco] WO {id_orden} {accion.value} -> ok={resultado.ok} {resultado.mensaje}", flush=True)
        except Exception as error:
            self.mensaje.setText(f"Error al enviar la orden: {error}")
            return

        self._feedback_visual(accion)
        self.refrescar_ordenes(mensaje=resultado.mensaje)

    def _feedback_visual(self, accion: Orden) -> None:
        boton = self.botones[accion]
        boton.setStyleSheet(self.get_style("#f39c12"))
        QTimer.singleShot(
            300,
            lambda: boton.setStyleSheet(self.get_style("#3498db")),
        )