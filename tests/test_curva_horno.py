# Ruta: tests/test_curva_horno.py en PC LAB
from centros_de_trabajo.politicas_ct.horno.modelo import PasoHorno, CurvaHorno


def test_curva_minima_valida():
    curva = CurvaHorno(rampa=PasoHorno(100, 800), enfriamiento=PasoHorno(20, 100))
    assert curva.es_valida()


def test_enfriamiento_obligatorio():
    curva = CurvaHorno(rampa=PasoHorno(100, 800), enfriamiento=None)
    assert not curva.es_valida()


def test_meseta_incompleta_falla():
    curva = CurvaHorno(
        rampa=PasoHorno(100, 800),
        meseta_temperatura=100,
        meseta_tiempo_minutos=None,
        enfriamiento=PasoHorno(20, 100),
    )
    assert not curva.es_valida()