from enum import Enum

from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


class Estado(Enum):
    NO_DISPONIBLE = "no_disponible"  # Odoo: pending / waiting
    DETENIDO = "detenido"            # Odoo: ready (lista, sin empezar)
    EN_CURSO = "en_curso"            # Odoo: progress, y yo tengo el cronómetro abierto
    PAUSADO = "pausado"              # Odoo: progress, y nadie está trabajando
    OCUPADO = "ocupado"              # Odoo: progress, y trabaja otro operario
    BLOQUEADO = "bloqueado"          # el centro de trabajo está bloqueado
    TERMINADO = "terminado"          # Odoo: done
    CANCELADO = "cancelado"          # Odoo: cancel


class OrdenInvalida(Exception):
    """Se intentó una orden que no corresponde al estado actual."""


# Qué orden es válida en cada estado y qué estado ESPERAMOS después.
# Ojo: el estado real lo informa Odoo; esto solo permite validar y comparar.
TRANSICIONES: dict[tuple[Estado, Orden], Estado] = {
    (Estado.DETENIDO, Orden.INICIAR): Estado.EN_CURSO,
    (Estado.EN_CURSO, Orden.PAUSAR): Estado.PAUSADO,
    (Estado.PAUSADO, Orden.REANUDAR): Estado.EN_CURSO,
    (Estado.EN_CURSO, Orden.TERMINAR): Estado.TERMINADO,
    (Estado.PAUSADO, Orden.TERMINAR): Estado.TERMINADO,
}


def derivar_estado(ot: OrdenDeTrabajo) -> Estado:
    """Traduce lo que dice Odoo a un Estado del kiosco. No guarda nada."""
    # Los estados finales mandan sobre todo lo demás.
    if ot.state == "done":
        return Estado.TERMINADO
    if ot.state == "cancel":
        return Estado.CANCELADO
    # La vista nativa de Odoo oculta los botones si el centro está bloqueado.
    if ot.working_state == "blocked":
        return Estado.BLOQUEADO
    if ot.state == "progress":
        if ot.is_user_working:
            return Estado.EN_CURSO
        return Estado.OCUPADO if ot.otros_trabajando else Estado.PAUSADO
    if ot.state == "ready":
        return Estado.DETENIDO
    if ot.state in ("pending", "waiting"):
        return Estado.NO_DISPONIBLE
    # Un valor que no conocemos no se esconde: se falla fuerte.
    raise ValueError(f"Estado de orden de trabajo desconocido: {ot.state!r}")


def puede(estado: Estado, orden: Orden) -> bool:
    return (estado, orden) in TRANSICIONES


def ordenes_validas(estado: Estado) -> frozenset[Orden]:
    """Para que la UI sepa qué botones habilitar."""
    return frozenset(o for (e, o) in TRANSICIONES if e == estado)


def estado_esperado(estado: Estado, orden: Orden) -> Estado:
    """Estado que esperamos tras la orden. Si no corresponde, lanza OrdenInvalida."""
    siguiente = TRANSICIONES.get((estado, orden))
    if siguiente is None:
        raise OrdenInvalida(f"{orden.value} no es válida estando {estado.value}")
    return siguiente