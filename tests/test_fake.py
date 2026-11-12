from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


def crear_wo(id_wo: int = 1) -> OrdenDeTrabajo:
    return OrdenDeTrabajo(
        id=id_wo,
        nombre=f"WO/{id_wo}",
        state="ready",
        is_user_working=False,
        working_state="normal",
    )


def test_fake_acepta_y_aplica_el_ciclo_completo():
    backend = FakeBackend([crear_wo()])

    for accion, estado_esperado in [
        (Orden.INICIAR, Estado.EN_CURSO),
        (Orden.PAUSAR, Estado.PAUSADO),
        (Orden.REANUDAR, Estado.EN_CURSO),
        (Orden.TERMINAR, Estado.TERMINADO),
    ]:
        resultado = backend.enviar(accion, 1)
        assert resultado.ok
        assert derivar_estado(backend.listar_ordenes()[0]) == estado_esperado


def test_fake_rechaza_orden_invalida_sin_cambiar_la_wo():
    backend = FakeBackend([crear_wo()])

    resultado = backend.enviar(Orden.PAUSAR, 1)

    assert not resultado.ok
    assert derivar_estado(backend.listar_ordenes()[0]) == Estado.DETENIDO


def test_fake_no_mezcla_el_estado_de_dos_wo():
    backend = FakeBackend([crear_wo(1), crear_wo(2)])

    assert backend.enviar(Orden.INICIAR, 1).ok

    ordenes = {orden.id: orden for orden in backend.listar_ordenes()}
    assert derivar_estado(ordenes[1]) == Estado.EN_CURSO
    assert derivar_estado(ordenes[2]) == Estado.DETENIDO