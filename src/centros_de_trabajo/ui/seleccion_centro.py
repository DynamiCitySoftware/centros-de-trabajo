# Ruta: src/centros_de_trabajo/ui/seleccion_centro.py en PC LAB
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.base import CentroDeTrabajo
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno


def construir_registro_centros() -> list[CentroDeTrabajo]:
    return [CentroHorno()]


def filtrar_ordenes_por_centro(
    centro_seleccionado: CentroDeTrabajo,
    todas_las_ordenes: list[OrdenDeTrabajo],
) -> list[OrdenDeTrabajo]:
    return [ot for ot in todas_las_ordenes if centro_seleccionado.es_mia(ot)]


def elegir_centro_por_nombre(
    nombre_odoo_buscado: str,
    registro_centros: list[CentroDeTrabajo],
) -> CentroDeTrabajo:
    for centro in registro_centros:
        if centro.nombre_odoo == nombre_odoo_buscado:
            return centro
    raise ValueError(f"No hay centro registrado con nombre_odoo={nombre_odoo_buscado!r}")