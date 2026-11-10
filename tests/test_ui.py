import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.core.estado import Estado, derivar_estado
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo
from centros_de_trabajo.ui.interfaz_principal import InterfazVenta


@pytest.fixture
def app():
    instancia = QApplication.instance() or QApplication([])
    yield instancia


@pytest.fixture
def backend():
    ordenes = [
        OrdenDeTrabajo(
            id=101,
            nombre="WO de prueba A",
            state="ready",
            is_user_working=False,
            working_state="normal",
        ),
        OrdenDeTrabajo(
            id=102,
            nombre="WO de prueba B",
            state="ready",
            is_user_working=False,
            working_state="normal",
        ),
    ]
    return FakeBackend(ordenes)


@pytest.fixture
def ventana(app, backend):
    ventana = InterfazVenta(backend)
    ventana.show()
    app.processEvents()
    yield ventana
    ventana.close()
    app.processEvents()


def seleccionar_wo(ventana, id_wo: int) -> None:
    for indice in range(ventana.lista_ordenes.count()):
        item = ventana.lista_ordenes.item(indice)
        if item.data(Qt.ItemDataRole.UserRole) == id_wo:
            ventana.lista_ordenes.setCurrentItem(item)
            return
    raise AssertionError(f"No aparece la WO {id_wo} en la UI")


def test_ui_carga_lista_y_habilita_acciones_iniciales(ventana):
    assert ventana.lista_ordenes.count() == 2
    assert ventana.botones[Orden.INICIAR].isEnabled()
    assert not ventana.botones[Orden.PAUSAR].isEnabled()
    assert not ventana.botones[Orden.REANUDAR].isEnabled()
    assert not ventana.botones[Orden.TERMINAR].isEnabled()


def test_ui_ejecuta_el_ciclo_completo_sobre_la_wo_seleccionada(
    ventana, backend
):
    ventana.botones[Orden.INICIAR].click()
    assert backend.listar_ordenes()[0].state == "progress"
    assert ventana.botones[Orden.PAUSAR].isEnabled()

    ventana.botones[Orden.PAUSAR].click()
    assert derivar_estado(backend.listar_ordenes()[0]) == Estado.PAUSADO
    assert ventana.botones[Orden.REANUDAR].isEnabled()

    ventana.botones[Orden.REANUDAR].click()
    assert backend.listar_ordenes()[0].is_user_working
    assert ventana.botones[Orden.TERMINAR].isEnabled()

    ventana.botones[Orden.TERMINAR].click()
    assert derivar_estado(backend.listar_ordenes()[0]) == Estado.TERMINADO
    assert all(not boton.isEnabled() for boton in ventana.botones.values())


def test_ui_acciones_de_una_wo_no_cambian_la_otra(ventana, backend):
    seleccionar_wo(ventana, 101)
    ventana.botones[Orden.INICIAR].click()

    seleccionar_wo(ventana, 102)
    assert ventana.botones[Orden.INICIAR].isEnabled()
    ventana.botones[Orden.INICIAR].click()

    ordenes = {orden.id: orden for orden in backend.listar_ordenes()}
    assert derivar_estado(ordenes[101]) == Estado.EN_CURSO
    assert derivar_estado(ordenes[102]) == Estado.EN_CURSO

    seleccionar_wo(ventana, 101)
    ventana.botones[Orden.PAUSAR].click()

    ordenes = {orden.id: orden for orden in backend.listar_ordenes()}
    assert derivar_estado(ordenes[101]) == Estado.PAUSADO
    assert derivar_estado(ordenes[102]) == Estado.EN_CURSO