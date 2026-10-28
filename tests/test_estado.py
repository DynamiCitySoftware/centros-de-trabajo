from itertools import product

import pytest

from centros_de_trabajo.core.estado import (
    TRANSICIONES,
    Estado,
    MaquinaDeEstados,
    OrdenInvalida,
)
from centros_de_trabajo.core.ordenes import Orden


def test_arranca_detenido():
    assert MaquinaDeEstados().estado == Estado.DETENIDO


def test_ciclo_completo():
    m = MaquinaDeEstados()
    assert m.aplicar(Orden.INICIAR) == Estado.EN_CURSO
    assert m.aplicar(Orden.PAUSAR) == Estado.PAUSADO
    assert m.aplicar(Orden.REANUDAR) == Estado.EN_CURSO
    assert m.aplicar(Orden.TERMINAR) == Estado.DETENIDO


# Todas las combinaciones (estado, orden) que NO están en la tabla
INVALIDAS = [c for c in product(Estado, Orden) if c not in TRANSICIONES]


@pytest.mark.parametrize("estado, orden", INVALIDAS)
def test_orden_invalida_falla_y_no_cambia_el_estado(estado, orden):
    m = MaquinaDeEstados(inicial=estado)
    assert not m.puede(orden)
    with pytest.raises(OrdenInvalida):
        m.aplicar(orden)
    assert m.estado == estado


def test_ordenes_validas_en_pausa():
    m = MaquinaDeEstados(inicial=Estado.PAUSADO)
    assert m.ordenes_validas() == {Orden.REANUDAR, Orden.TERMINAR}