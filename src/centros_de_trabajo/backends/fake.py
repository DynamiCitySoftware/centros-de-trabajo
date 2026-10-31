from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden


class FakeBackend:
    """Backend de prueba: no usa red, solo registra las órdenes."""

    def __init__(self) -> None:
        self.enviadas: list[tuple[Orden, int]] = []

    def enviar(self, orden: Orden, id_orden: int) -> Resultado:
        self.enviadas.append((orden, id_orden))
        print(f"[fake] orden: {orden.value} sobre WO {id_orden}")
        return Resultado(True, f"(fake) {orden.value} registrada")