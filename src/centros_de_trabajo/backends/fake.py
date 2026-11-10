from dataclasses import replace

from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.estado import (
    Estado,
    OrdenInvalida,
    derivar_estado,
    estado_esperado,
    puede,
)
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


class FakeBackend:
    """Backend en memoria para probar la aplicación sin red ni Odoo."""

    def __init__(self, ordenes: list[OrdenDeTrabajo] | None = None) -> None:
        ordenes_iniciales = ordenes if ordenes is not None else []
        self._ordenes = {orden.id: orden for orden in ordenes_iniciales}

        if len(self._ordenes) != len(ordenes_iniciales):
            raise ValueError("Las órdenes de prueba deben tener IDs únicos.")

        self.enviadas: list[tuple[Orden, int]] = []

    def listar_ordenes(self) -> list[OrdenDeTrabajo]:
        """Devuelve una copia ordenada por ID; no expone el diccionario interno."""
        return [self._ordenes[id_wo] for id_wo in sorted(self._ordenes)]

    def enviar(self, orden: Orden, id_orden: int) -> Resultado:
        """Valida y aplica una acción sobre una WO en memoria."""
        self.enviadas.append((orden, id_orden))

        actual = self._ordenes.get(id_orden)
        if actual is None:
            return Resultado(False, f"No existe la WO {id_orden} en el FakeBackend.")

        try:
            estado_actual = derivar_estado(actual)
            siguiente = estado_esperado(estado_actual, orden)
        except (OrdenInvalida, ValueError) as error:
            return Resultado(False, str(error))

        if not puede(estado_actual, orden):
            return Resultado(
                False,
                f"{orden.value} no es válida estando {estado_actual.value}",
            )

        if orden in (Orden.INICIAR, Orden.REANUDAR):
            actualizado = replace(
                actual,
                state="progress",
                is_user_working=True,
                otros_trabajando=False,
            )
        elif orden == Orden.PAUSAR:
            actualizado = replace(
                actual,
                state="progress",
                is_user_working=False,
                otros_trabajando=False,
            )
        elif orden == Orden.TERMINAR:
            actualizado = replace(
                actual,
                state="done",
                is_user_working=False,
                otros_trabajando=False,
            )
        else:
            return Resultado(False, f"Orden no implementada: {orden!r}")

        self._ordenes[id_orden] = actualizado
        return Resultado(True, f"{orden.value} aplicada ({siguiente.value})")