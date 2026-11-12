# Ruta: src/centros_de_trabajo/ui/ui_horno.py en PC LAB
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.base import EstadoKiosco
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno
from centros_de_trabajo.politicas_ct.horno.mock_horno import MockHorno
from centros_de_trabajo.politicas_ct.horno.modelo import CurvaHorno, PasoHorno


class VentanaHorno(QMainWindow):
    def __init__(
        self,
        backend_a_usar: Backend,
        centro_horno_a_usar: CentroHorno,
        horno_fisico_o_mock: MockHorno,
    ) -> None:
        super().__init__()
        self._backend = backend_a_usar
        self._centro = centro_horno_a_usar
        self._horno = horno_fisico_o_mock
        self.setWindowTitle("Horno Microondas - Kiosco")
        self.showFullScreen()

        contenedor = QWidget()
        layout = QVBoxLayout()
        self._etiqueta_estado = QLabel("Sin selección")
        self._lista_ordenes = QListWidget()
        self._boton_iniciar = QPushButton("INICIAR [F1]")
        self._boton_terminar = QPushButton("TERMINAR [F2]")
        self._boton_abortar = QPushButton("ABORTAR [F3]")
        layout.addWidget(self._etiqueta_estado)
        layout.addWidget(self._lista_ordenes)
        layout.addWidget(self._boton_iniciar)
        layout.addWidget(self._boton_terminar)
        layout.addWidget(self._boton_abortar)
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        self._boton_iniciar.clicked.connect(lambda: self._al_presionar(Orden.INICIAR))
        self._boton_terminar.clicked.connect(lambda: self._al_presionar(Orden.TERMINAR))
        self._boton_abortar.clicked.connect(lambda: self._al_presionar(Orden.ABORTAR))
        self.recargar_lista()

    def recargar_lista(self) -> None:
        self._lista_ordenes.clear()
        self._ordenes_visibles: list[OrdenDeTrabajo] = [
            ot for ot in self._backend.listar_ordenes() if self._centro.es_mia(ot)
        ]
        for ot in self._ordenes_visibles:
            estado = self._centro.derivar_estado(ot)
            self._lista_ordenes.addItem(f"WO {ot.id_odoo} {ot.operacion_nombre} {estado.value}")

    def _orden_seleccionada(self) -> OrdenDeTrabajo | None:
        fila = self._lista_ordenes.currentRow()
        if fila < 0 or fila >= len(self._ordenes_visibles):
            return None
        return self._ordenes_visibles[fila]

    def _al_presionar(self, orden_solicitada: Orden) -> None:
        ot = self._orden_seleccionada()
        if ot is None:
            self._etiqueta_estado.setText("Elegí una WO primero")
            return
        estado_actual = self._centro.derivar_estado(ot)
        if orden_solicitada not in self._centro.ordenes_validas(estado_actual):
            self._etiqueta_estado.setText(f"{orden_solicitada.value} no permitido en {estado_actual.value}")
            return
        if orden_solicitada == Orden.INICIAR:
            # Curva genérica para probar flujo end to end, no valores de producción
            curva_generica = CurvaHorno(
                rampa=PasoHorno(temperatura_objetivo=100, potencia=800),
                enfriamiento=PasoHorno(temperatura_objetivo=20, potencia=100),
            )
            errores = self._horno.iniciar_curva(curva_generica)
            if errores:
                self._etiqueta_estado.setText(f"Curva inválida: {errores}")
                return
        if orden_solicitada == Orden.ABORTAR:
            self._horno.abortar()
        resultado = self._backend.enviar(orden_solicitada, ot.id_odoo)
        self._etiqueta_estado.setText(resultado.mensaje)
        self.recargar_lista()