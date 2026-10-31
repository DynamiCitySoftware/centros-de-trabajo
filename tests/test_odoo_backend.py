import xmlrpc.client
from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.core.ordenes import Orden


def registro_listo():
    return {"id": 14, "name": "operacion", "state": "ready", "is_user_working": False,
            "working_state": "normal", "working_user_ids": []}


class OdooSimulado(OdooBackend):
    """Imita lo medido contra el Odoo real. No hace ninguna llamada de red."""

    def __init__(self, registro, rechaza=None, ignora_botones=False):
        super().__init__("http://no-se-usa", "db", "usuario", Path("/no/existe"))
        self._uid = 18
        self.registro = registro
        self.rechaza = rechaza
        self.ignora_botones = ignora_botones
        self.llamadas = []

    def _ejecutar(self, modelo, metodo, args, kwargs=None):
        self.llamadas.append(metodo)
        if metodo == "read":
            return [dict(self.registro)] if self.registro else []
        if self.rechaza:
            raise xmlrpc.client.Fault(2, self.rechaza)
        if self.ignora_botones:
            return True
        if metodo == "button_start":
            self.registro.update(state="progress", is_user_working=True, working_user_ids=[18])
            raise xmlrpc.client.Fault(1, "TypeError: cannot marshal None unless allow_none is enabled")
        if metodo == "button_pending":
            self.registro.update(is_user_working=False, working_user_ids=[])
            raise xmlrpc.client.Fault(1, "TypeError: cannot marshal None unless allow_none is enabled")
        if metodo == "button_finish":
            self.registro.update(state="done", is_user_working=False, working_user_ids=[])
            return True
        raise AssertionError(f"método inesperado: {metodo}")


def test_ciclo_completo():
    odoo = OdooSimulado(registro_listo())
    for orden in (Orden.INICIAR, Orden.PAUSAR, Orden.REANUDAR, Orden.TERMINAR):
        resultado = odoo.enviar(orden, 14)
        assert resultado.ok, resultado.mensaje
    assert odoo.registro["state"] == "done"


def test_orden_invalida_no_escribe_en_odoo():
    odoo = OdooSimulado(registro_listo())
    resultado = odoo.enviar(Orden.PAUSAR, 14)   # una WO 'ready' no se puede pausar
    assert not resultado.ok
    assert "button_pending" not in odoo.llamadas


def test_orden_inexistente():
    resultado = OdooSimulado(None).enviar(Orden.INICIAR, 999)
    assert not resultado.ok
    assert "999" in resultado.mensaje


def test_fault_real_se_informa_y_no_se_traga():
    odoo = OdooSimulado(registro_listo(), rechaza="You cannot start a work order that is already done")
    resultado = odoo.enviar(Orden.INICIAR, 14)
    assert not resultado.ok
    assert "Odoo rechazó" in resultado.mensaje


def test_si_odoo_no_refleja_el_cambio_falla():
    odoo = OdooSimulado(registro_listo(), ignora_botones=True)
    resultado = odoo.enviar(Orden.INICIAR, 14)
    assert not resultado.ok
    assert "no reflejó" in resultado.mensaje