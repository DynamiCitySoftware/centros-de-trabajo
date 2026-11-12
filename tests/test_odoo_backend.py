# Ruta: tests/test_odoo_backend.py en PC LAB
from unittest.mock import MagicMock
from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.core.ordenes import Orden


def _backend_mockeado(registros):
    backend = OdooBackend.__new__(OdooBackend)
    backend._uid = 18
    backend._ejecutar = MagicMock(return_value=registros)
    # _autenticar no hace nada en test, ya hay uid
    backend._autenticar = lambda: None  # type: ignore
    return backend


def _registro_horno(id_odoo=34):
    return {
        "id": id_odoo,
        "name": "horneado simple",
        "state": "ready",
        "is_user_working": False,
        "working_state": "normal",
        "working_user_ids": [],
        "workcenter_id": [5, "Horno Microondas"],
        "duration": 0.0,
    }


def test_listar_mapea_workcenter_y_duracion():
    backend = _backend_mockeado([_registro_horno(34), _registro_horno(35)])
    ordenes = backend.listar_ordenes()
    assert [o.id_odoo for o in ordenes] == [34, 35]
    assert ordenes[0].workcenter_nombre == "Horno Microondas"
    assert ordenes[0].operacion_nombre == "horneado simple"
    assert ordenes[0].duracion_minutos == 0.0


def test_enviar_llama_boton_correcto():
    backend = _backend_mockeado([_registro_horno(34)])
    # leer_orden devuelve el registro, _llamar_boton no hace nada
    backend.leer_orden = lambda i: _registro_horno(i)  # type: ignore
    backend._llamar_boton = MagicMock(return_value=None)  # type: ignore
    # solo comprobamos mapeo INICIAR->button_start y TERMINAR->button_finish
    from centros_de_trabajo.backends.odoo import BOTON_POR_ORDEN
    assert BOTON_POR_ORDEN[Orden.INICIAR] == "button_start"
    assert BOTON_POR_ORDEN[Orden.TERMINAR] == "button_finish"