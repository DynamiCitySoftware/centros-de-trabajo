from dataclasses import dataclass
from typing import Protocol

from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo


@dataclass(frozen=True)
class Resultado:
    ok: bool
    mensaje: str


class Backend(Protocol):
    def listar_ordenes(self) -> list[OrdenDeTrabajo]: ...
    def enviar(self, orden: Orden, wo_id: int | None = None) -> Resultado: ...