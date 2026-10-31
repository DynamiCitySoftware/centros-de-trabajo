import pytest

from centros_de_trabajo.core.estado import cumple_postcondicion
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


def ot(state, trabajando):
    return OrdenDeTrabajo(id=1, nombre="WO/1", state=state, is_user_working=trabajando,
                          working_state="normal")


@pytest.mark.parametrize("orden, state, trabajando, esperado", [
    (Orden.INICIAR, "progress", True, True),
    (Orden.INICIAR, "ready", False, False),
    (Orden.REANUDAR, "progress", True, True),
    (Orden.REANUDAR, "progress", False, False),
    (Orden.PAUSAR, "progress", False, True),
    (Orden.PAUSAR, "progress", True, False),
    (Orden.TERMINAR, "done", False, True),
    (Orden.TERMINAR, "progress", False, False),
])
def test_postcondicion(orden, state, trabajando, esperado):
    assert cumple_postcondicion(orden, ot(state, trabajando)) is esperado