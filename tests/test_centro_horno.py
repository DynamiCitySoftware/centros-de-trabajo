# Ruta: tests/test_centro_horno.py en PC LAB
from centros_de_trabajo.politicas_ct.base import EstadoKiosco, Orden
from centros_de_trabajo.politicas_ct.horno.centro_horno import CentroHorno


class OrdenFalsaParaTest:
    def __init__(self, estado_odoo, con_cronometro=False):
        self.estado_odoo = estado_odoo
        self.existe_cronometro_para_usuario = con_cronometro
        self.usuario_es_responsable = con_cronometro
        self.workcenter_nombre = "Horno Microondas"
        self.operacion_nombre = "horneado simple"
        self.duracion_minutos = 0.0


def test_ready_es_detenido_y_solo_iniciar():
    centro = CentroHorno()
    orden = OrdenFalsaParaTest("ready")
    assert centro.derivar_estado(orden) == EstadoKiosco.DETENIDO
    assert centro.ordenes_validas(EstadoKiosco.DETENIDO) == {Orden.INICIAR}


def test_en_curso_permite_terminar_pero_no_pausar():
    centro = CentroHorno()
    orden = OrdenFalsaParaTest("progress", con_cronometro=True)
    assert centro.derivar_estado(orden) == EstadoKiosco.EN_CURSO
    validas = centro.ordenes_validas(EstadoKiosco.EN_CURSO)