from itertools import product

import pytest

from centros_de_trabajo.core.estado import (
    TRANSICIONES,
    Estado,
    OrdenInvalida,
    derivar_estado,
    estado_esperado,
    ordenes_validas,
)
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


def ot(state, trabajando=False, centro="normal", otros=False):
    return OrdenDeTrabajo(id=1, nombre="WO/1", state=state, is_user_working=trabajando,
                          working_state=centro, otros_trabajando=otros)


@pytest.mark.parametrize("state, trabajando, centro, otros, esperado", [
    ("ready", False, "normal", False, Estado.DETENIDO),
    ("progress", True, "done", False, Estado.EN_CURSO),
    ("progress", True, "done", True, Estado.EN_CURSO),
    ("progress", False, "normal", False, Estado.PAUSADO),
    ("progress", False, "done", True, Estado.OCUPADO),
    ("progress", False, "blocked", False, Estado.BLOQUEADO),
    ("ready", False, "blocked", False, Estado.BLOQUEADO),
    ("pending", False, "normal", False, Estado.NO_DISPONIBLE),
    ("waiting", False, "normal", False, Estado.NO_DISPONIBLE),
    ("done", False, "blocked", False, Estado.TERMINADO),
    ("cancel", False, "blocked", False, Estado.CANCELADO),
])
def test_derivar_estado(state, trabajando, centro, otros, esperado):
    assert derivar_estado(ot(state, trabajando, centro, otros)) == esperado


def test_estado_desconocido_falla():
    with pytest.raises(ValueError):
        derivar_estado(ot("inventado"))


def test_ciclo_completo_esperado():
    e = Estado.DETENIDO
    for orden, siguiente in [(Orden.INICIAR, Estado.EN_CURSO), (Orden.PAUSAR, Estado.PAUSADO),
                             (Orden.REANUDAR, Estado.EN_CURSO), (Orden.TERMINAR, Estado.TERMINADO)]:
        e = estado_esperado(e, orden)
        assert e == siguiente


# Todas las combinaciones (estado, orden) que NO están en la tabla
INVALIDAS = [c for c in product(Estado, Orden) if c not in TRANSICIONES]


@pytest.mark.parametrize("estado, orden", INVALIDAS)
def test_orden_invalida_falla(estado, orden):
    with pytest.raises(OrdenInvalida):
        estado_esperado(estado, orden)


def test_ordenes_validas_en_pausa():
    assert ordenes_validas(Estado.PAUSADO) == {Orden.REANUDAR, Orden.TERMINAR}


def test_estados_finales_no_aceptan_ordenes():
    assert ordenes_validas(Estado.TERMINADO) == frozenset()
    assert ordenes_validas(Estado.OCUPADO) == frozenset()


def test_desde_odoo_distingue_otros_usuarios():
    registro = {"id": 7, "name": "Corte", "state": "progress", "is_user_working": False,
                "working_state": "done", "working_user_ids": [18, 20]}
    assert OrdenDeTrabajo.desde_odoo(registro, uid=18).otros_trabajando is True
    registro["working_user_ids"] = [18]
    assert OrdenDeTrabajo.desde_odoo(registro, uid=18).otros_trabajando is False