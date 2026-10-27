from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden


class FakeBackend:
    """Backend de prueba: no usa red, solo registra las órdenes."""

    def __init__(self) -> None:
        self.enviadas: list[Orden] = []

    def enviar(self, orden: Orden) -> Resultado:
        self.enviadas.append(orden)
        print(f"[fake] orden: {orden.value}")
        return Resultado(True, f"(fake) {orden.value} registrada")