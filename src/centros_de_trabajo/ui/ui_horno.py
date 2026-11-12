# Ruta: src/centros_de_trabajo/ui/ui_horno.py en PC LAB - reemplazar TODO el archivo
import traceback
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QFormLayout, QListWidget, QPushButton, QLabel, QLineEdit

from centros_de_trabajo.backends.base import Backend
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno
from centros_de_trabajo.politicas_ct.horno.mock_horno import MockHorno
from centros_de_trabajo.politicas_ct.horno.modelo import CurvaHorno, PasoHorno


def construir_curva_desde_textos(
    rampa_temp_txt: str,
    rampa_pot_txt: str,
    enfriamiento_temp_txt: str,
    enfriamiento_pot_txt: str,
    meseta_temp_txt: str,
    meseta_tiempo_txt: str,
) -> CurvaHorno:
    """Convierte textos de la UI en CurvaHorno. Textos vacíos de meseta = None."""
    def a_float(txt: str, defecto: float) -> float:
        txt = txt.strip().replace(",", ".")
        return float(txt) if txt else defecto

    def a_int(txt: str, defecto: int) -> int:
        txt = txt.strip()
        return int(float(txt)) if txt else defecto

    meseta_temp_txt = meseta_temp_txt.strip()
    meseta_tiempo_txt = meseta_tiempo_txt.strip()
    tiene_meseta = bool(meseta_temp_txt) or bool(meseta_tiempo_txt)
    return CurvaHorno(
        rampa=PasoHorno(
            temperatura_objetivo=a_float(rampa_temp_txt, 100.0),
            potencia=a_int(rampa_pot_txt, 800),
        ),
        enfriamiento=PasoHorno(
            temperatura_objetivo=a_float(enfriamiento_temp_txt, 20.0),
            potencia=a_int(enfriamiento_pot_txt, 100),
        ),
        meseta_temperatura=a_float(meseta_temp_txt, 0.0) if tiene_meseta else None,
        meseta_tiempo_minutos=a_float(meseta_tiempo_txt, 0.0) if tiene_meseta else None,
    )


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

        formulario = QFormLayout()
        self._campo_rampa_temp = QLineEdit("100")
        self._campo_rampa_pot = QLineEdit("800")
        self._campo_enfriamiento_temp = QLineEdit("20")
        self._campo_enfriamiento_pot = QLineEdit("100")
        self._campo_meseta_temp = QLineEdit("")
        self._campo_meseta_tiempo = QLineEdit("")
        self._campo_rampa_temp.setPlaceholderText("VALOR_GENERICO_TEMP, ej 100")
        self._campo_enfriamiento_temp.setPlaceholderText("VALOR_GENERICO_TEMP, ej 20")
        self._campo_meseta_temp.setPlaceholderText("opcional")
        self._campo_meseta_tiempo.setPlaceholderText("opcional en minutos")
        formulario.addRow("Rampa temp objetivo:", self._campo_rampa_temp)
        formulario.addRow("Rampa potencia:", self._campo_rampa_pot)
        formulario.addRow("Enfriamiento temp:", self._campo_enfriamiento_temp)
        formulario.addRow("Enfriamiento potencia:", self._campo_enfriamiento_pot)
        formulario.addRow("Meseta temp (opcional):", self._campo_meseta_temp)
        formulario.addRow("Meseta tiempo min (opcional):", self._campo_meseta_tiempo)

        self._boton_iniciar = QPushButton("INICIAR [F1]")
        self._boton_terminar = QPushButton("TERMINAR [F2]")
        layout.addWidget(self._etiqueta_estado)
        layout.addLayout(formulario)
        layout.addWidget(self._lista_ordenes)
        layout.addWidget(self._boton_iniciar)
        layout.addWidget(self._boton_terminar)
        contenedor.setLayout(layout)
        self.setCentralWidget(contenedor)

        self._boton_iniciar.clicked.connect(lambda: self._al_presionar(Orden.INICIAR))
        self._boton_terminar.clicked.connect(lambda: self._al_presionar(Orden.TERMINAR))
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

    def _leer_curva_desde_ui(self) -> CurvaHorno:
        return construir_curva_desde_textos(
            self._campo_rampa_temp.text(),
            self._campo_rampa_pot.text(),
            self._campo_enfriamiento_temp.text(),
            self._campo_enfriamiento_pot.text(),
            self._campo_meseta_temp.text(),
            self._campo_meseta_tiempo.text(),
        )

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
                try:
                    curva_cargada = self._leer_curva_desde_ui()
                except ValueError as e:
                    self._etiqueta_estado.setText(f"Curva con números inválidos: {e}")
                    return
                print(f"[ui_horno] curva leída rampa={curva_cargada.rampa} enf={curva_cargada.enfriamiento} meseta={curva_cargada.meseta_temperatura}/{curva_cargada.meseta_tiempo_minutos}", flush=True)
                errores = self._horno.iniciar_curva(curva_cargada)
                print(f"[ui_horno] mock iniciar ret={errores}", flush=True)
                if errores:
                    self._etiqueta_estado.setText(f"Curva inválida: {errores}")
                    return
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