from enum import Enum

from centros_de_trabajo.core.ordenes import Orden


class Estado(Enum):
    DETENIDO = "detenido"
    EN_CURSO = "en_curso"
    PAUSADO = "pausado"


class OrdenInvalida(Exception):
    """Se intentó una orden que no corresponde al estado actual."""


# Todas las reglas del negocio
TRANSICIONES: dict[tuple[Estado, Orden], Estado] = {
    (Estado.DETENIDO, Orden.INICIAR): Estado.EN_CURSO,
    (Estado.EN_CURSO, Orden.PAUSAR): Estado.PAUSADO,
    (Estado.PAUSADO, Orden.REANUDAR): Estado.EN_CURSO,
    (Estado.EN_CURSO, Orden.TERMINAR): Estado.DETENIDO,
    (Estado.PAUSADO, Orden.TERMINAR): Estado.DETENIDO,
}


class MaquinaDeEstados:
    def __init__(self, inicial: Estado = Estado.DETENIDO) -> None:
        self._estado = inicial

    @property
    def estado(self) -> Estado:
        return self._estado

    def puede(self, orden: Orden) -> bool:
        """¿Es válida esta orden en el estado actual? No cambia nada."""
        return (self._estado, orden) in TRANSICIONES

    def ordenes_validas(self) -> frozenset[Orden]:
        """Para que la UI sepa qué botones habilitar."""
        return frozenset(o for (e, o) in TRANSICIONES if e == self._estado)

    def aplicar(self, orden: Orden) -> Estado:
        """Cambia de estado. Si la orden no corresponde, lanza OrdenInvalida y no toca nada."""
        siguiente = TRANSICIONES.get((self._estado, orden))
        if siguiente is None:
            raise OrdenInvalida(f"{orden.value} no es válida estando {self._estado.value}")
        self._estado = siguiente
        return siguiente