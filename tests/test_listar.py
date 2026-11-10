from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend
from centros_de_trabajo.core.ordenes import OrdenDeTrabajo


def fila(id_wo: int, state: str = "ready") -> dict:
    return {
        "id": id_wo,
        "name": f"WO/{id_wo}",
        "state": state,
        "is_user_working": False,
        "working_state": "normal",
        "working_user_ids": [],
    }


class OdooListadoSimulado(OdooBackend):
    def __init__(self, filas: list[dict]) -> None:
        super().__init__(
            "http://no-se-usa",
            "db",
            "usuario",
            Path("/no/existe"),
        )
        self._uid = 19
        self._filas = filas
        self.llamadas = []

    def _ejecutar(self, modelo, metodo, args, kwargs=None):
        assert modelo == "mrp.workorder"
        assert metodo == "search_read"

        opciones = kwargs or {}
        self.llamadas.append((args[0], opciones.copy()))

        offset = opciones["offset"]
        limite = opciones["limit"]
        return self._filas[offset:offset + limite]


def test_listar_incluye_ready_done_responsable_y_tiempo(monkeypatch):
    monkeypatch.setattr("centros_de_trabajo.backends.odoo.TAMANO_PAGINA_LISTADO", 2)

    filas = [
        fila(21, "ready"),
        fila(22, "ready"),
        fila(23, "done"),
        fila(24, "progress"),
        fila(25, "progress"),
    ]
    backend = OdooListadoSimulado(filas)

    ordenes = backend.listar_ordenes()

    assert [orden.id for orden in ordenes] == [21, 22, 23, 24, 25]
    assert all(isinstance(orden, OrdenDeTrabajo) for orden in ordenes)

    # Cuatro criterios, combinados con OR:
    # ready | done | MO asignada al usuario | cronómetro del usuario.
    dominio_esperado = [
        "|", "|", "|",
        ("state", "=", "ready"),
        ("state", "=", "done"),
        ("production_id.user_id", "=", 19),
        ("time_ids.user_id", "=", 19),
    ]
    assert all(dominio == dominio_esperado for dominio, _ in backend.llamadas)

    # El tamaño de página de prueba es 2: 2, 2 y 1 filas.
    assert [opciones["offset"] for _, opciones in backend.llamadas] == [0, 2, 4]
    assert all(opciones["limit"] == 2 for _, opciones in backend.llamadas)
    assert all(opciones["order"] == "id asc" for _, opciones in backend.llamadas)

    # No debe haber duplicados en el resultado.
    assert len({orden.id for orden in ordenes}) == len(ordenes)