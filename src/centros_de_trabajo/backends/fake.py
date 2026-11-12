# Ruta: src/centros_de_trabajo/backends/fake.py en PC LAB
from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


class FakeBackend:
    """Backend en memoria para probar la app sin red ni Odoo."""

    def __init__(self, ordenes: list[OrdenDeTrabajo] | None = None) -> None:
        ordenes_iniciales = ordenes if ordenes is not None else []
        self._ordenes: dict[int, OrdenDeTrabajo] = {
            o.id_odoo: o for o in ordenes_iniciales
        }
        if len(self._ordenes) != len(ordenes_iniciales):
            raise ValueError("Las órdenes de prueba deben tener id_odoo único.")
        self.enviadas: list[tuple[Orden, int]] = []

    def listar_ordenes(self) -> list[OrdenDeTrabajo]:
        return [self._ordenes[k] for k in sorted(self._ordenes)]

    def enviar(self, orden: Orden, id_orden: int) -> Resultado:
        actual = self._ordenes.get(id_orden)
        if actual is None:
            return Resultado(False, f"No existe la WO {id_orden} en el FakeBackend.")
        self.enviadas.append((orden, id_orden))
        return Resultado(True, f"{orden.value} aplicada ({id_orden})")