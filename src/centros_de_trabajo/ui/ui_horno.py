# Ruta: src/centros_de_trabajo/ui/ui_horno.py en PC LAB - reemplazar TODO el archivo
import traceback
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QListWidget, QPushButton, QLabel

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno
from centros_de_trabajo.politicas_ct.horno.mock_horno import MockHorno
from centros_de_trabajo.politicas_ct.horno.modelo import CurvaHorno, PasoHorno


class VentanaHorno(QMainWindow):
    def __init__(self, backend_a_usar: Backend, centro_horno_a_usar: CentroHorno, horno_fisico_o_mock: MockHorno) -> None:
        super().__init__()
        self._backend = backend_a_usar
        self._centro = centro_horno_a_usar
        self._horno = horno_fisico_o_mock
        self.setWindowTitle("Horno Microondas - Kiosco")
        self.showFullScreen()
        print("[ui_horno] init ventana", flush=True)

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
        print("[ui_horno] recargar_lista inicio", flush=True)
        try:
            todas = self._backend.listar_ordenes()
            print(f"[ui_horno] backend trajo {len(todas)} ordenes", flush=True)
            self._lista_ordenes.clear()
            self._ordenes_visibles: list[OrdenDeTrabajo] = [ot for ot in todas if self._centro.es_mia(ot)]
            print(f"[ui_horno] filtradas por horno: {len(self._ordenes_visibles)}", flush=True)
            for ot in self._ordenes_visibles:
                estado = self._centro.derivar_estado(ot)
                print(f"[ui_horno] WO {ot.id_odoo} {ot.operacion_nombre} odoo={ot.estado_odoo} kiosco={estado.value}", flush=True)
                self._lista_ordenes.addItem(f"WO {ot.id_odoo} {ot.operacion_nombre} {estado.value}")
            print("[ui_horno] recargar_lista fin", flush=True)
        except Exception as e:
            print(f"[ui_horno] EXCEPCION en recargar_lista: {e}", flush=True)
            traceback.print_exc()
            self._etiqueta_estado.setText(f"Error listando: {e}")

    def _orden_seleccionada(self) -> OrdenDeTrabajo | None:
        fila = self._lista_ordenes.currentRow()
        if fila < 0 or fila >= len(self._ordenes_visibles):
            return None
        return self._ordenes_visibles[fila]

    def _al_presionar(self, orden_solicitada: Orden) -> None:
        print(f"[ui_horno] click {orden_solicitada.value}", flush=True)
        try:
            ot = self._orden_seleccionada()
            print(f"[ui_horno] seleccionada: {ot}", flush=True)
            if ot is None:
                self._etiqueta_estado.setText("Elegí una WO primero")
                return
            estado_actual = self._centro.derivar_estado(ot)
            print(f"[ui_horno] estado_actual={estado_actual.value} validas={self._centro.ordenes_validas(estado_actual)}", flush=True)
            if orden_solicitada not in self._centro.ordenes_validas(estado_actual):
                self._etiqueta_estado.setText(f"{orden_solicitada.value} no permitido en {estado_actual.value}")
                return
            if orden_solicitada == Orden.INICIAR:
                curva_generica = CurvaHorno(
                    rampa=PasoHorno(temperatura_objetivo=100, potencia=800),
                    enfriamiento=PasoHorno(temperatura_objetivo=20, potencia=100),
                )
                print("[ui_horno] iniciando mock horno", flush=True)
                errores = self._horno.iniciar_curva(curva_generica)
                print(f"[ui_horno] mock iniciar ret={errores}", flush=True)
                if errores:
                    self._etiqueta_estado.setText(f"Curva inválida: {errores}")
                    return
            if orden_solicitada == Orden.ABORTAR:
                print("[ui_horno] abortando mock", flush=True)
                self._horno.abortar()
            print(f"[ui_horno] enviando a backend {orden_solicitada.value} WO {ot.id_odoo}", flush=True)
            resultado = self._backend.enviar(orden_solicitada, ot.id_odoo)
            print(f"[ui_horno] backend ret ok={resultado.ok} msg={resultado.mensaje}", flush=True)
            self._etiqueta_estado.setText(resultado.mensaje)
            print("[ui_horno] recargando lista post-envio", flush=True)
            self.recargar_lista()
            print("[ui_horno] click fin", flush=True)
        except Exception as e:
            print(f"[ui_horno] EXCEPCION en click {orden_solicitada.value}: {e}", flush=True)
            traceback.print_exc()
            self._etiqueta_estado.setText(f"Error: {e}")