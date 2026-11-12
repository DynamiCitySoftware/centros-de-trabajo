# Ruta: src/centros_de_trabajo/politicas_ct/horno/centro_horno.py en PC LAB
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo
from centros_de_trabajo.politicas_ct.base import CentroDeTrabajo, EstadoKiosco, Orden


class CentroHorno(CentroDeTrabajo):
    nombre_odoo = "Horno Microondas"  # confirmado por tus WO 34/35/38
    operaciones_soportadas = ["horneado simple"]  # de tu BoM de Pan

    def derivar_estado(self, orden_de_trabajo: OrdenDeTrabajo) -> EstadoKiosco:
        if orden_de_trabajo.estado_odoo == "done":
            return EstadoKiosco.TERMINADO
        if orden_de_trabajo.estado_odoo == "cancel":
            return EstadoKiosco.ABORTADO
        if orden_de_trabajo.estado_odoo == "progress" and orden_de_trabajo.existe_cronometro_para_usuario:
            return EstadoKiosco.EN_CURSO
        if orden_de_trabajo.estado_odoo in ("ready", "progress"):
            return EstadoKiosco.DETENIDO
        return EstadoKiosco.NO_DISPONIBLE

    def ordenes_validas(self, estado_kiosco: EstadoKiosco) -> set[Orden]:
        if estado_kiosco == EstadoKiosco.DETENIDO:
            return {Orden.INICIAR}
        if estado_kiosco == EstadoKiosco.EN_CURSO:
            return {Orden.TERMINAR}
        return set()

    def tiempo_proceso_minutos(self, orden_de_trabajo: OrdenDeTrabajo) -> float:
        return orden_de_trabajo.duracion_minutos

    def tiempo_operacion_minutos(self, inicio_timestamp: float, fin_timestamp: float) -> float:
        return (fin_timestamp - inicio_timestamp) / 60.0