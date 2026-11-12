# Ruta: tests/test_seleccion_centro.py en PC LAB
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.ui.seleccion_centro import (
    construir_registro_centros,
    elegir_centro_por_nombre,
    filtrar_ordenes_por_centro,
)


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


def _orden_torno(id_odoo=21):
    return OrdenDeTrabajo(
        id_odoo=id_odoo,
        operacion_nombre="torneado piola",
        estado_odoo="ready",
        workcenter_nombre="Torno Naranja 450mm",
        usuario_es_responsable=False,
        existe_cronometro_para_usuario=False,
        duracion_minutos=0.0,
    )


def test_seleccion_filtra_solo_horno():
    centro = elegir_centro_por_nombre("Horno Microondas", construir_registro_centros())
    visibles = filtrar_ordenes_por_centro(centro, [_orden_horno(34), _orden_torno(21)])
    assert [o.id_odoo for o in visibles] == [34]