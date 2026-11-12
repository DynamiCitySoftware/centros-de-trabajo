# Ruta: tests/test_fake.py en PC LAB
from centros_de_trabajo.backends.fake import FakeBackend
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


def _orden_horno(id_odoo=34):
    return OrdenDeTrabajo(
        id_odoo=id_odoo,
        operacion_nombre="horneado simple",
        estado_odoo="ready",
        workcenter_nombre="Horno Microondas",
        usuario_es_responsable=False,
        existe_cronometro_para_usuario=False,
        duracion_minutos=0.0,
    )


def test_fake_lista_ordenado_por_id():
    backend = FakeBackend([_orden_horno(35), _orden_horno(34)])
    assert [o.id_odoo for o in backend.listar_ordenes()] == [34, 35]


def test_fake_acepta_las_ordenes_del_horno():
    backend = FakeBackend([_orden_horno(34)])
    for orden in [Orden.INICIAR, Orden.TERMINAR, Orden.ABORTAR]:
        resultado = backend.enviar(orden, 34)
        assert resultado.ok
    assert backend.enviadas == [
        (Orden.INICIAR, 34),
        (Orden.TERMINAR, 34),
        (Orden.ABORTAR, 34),
    ]


def test_fake_rechaza_wo_inexistente():
    backend = FakeBackend([])
    assert not backend.enviar(Orden.INICIAR, 999).ok