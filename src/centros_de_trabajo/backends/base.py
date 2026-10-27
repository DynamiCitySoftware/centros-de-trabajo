from dataclasses import dataclass
from typing import Protocol

from centros_de_trabajo.core.ordenes import Orden


@dataclass(frozen=True)
class Resultado:
    ok: bool
    mensaje: str


class Backend(Protocol):
    def enviar(self, orden: Orden) -> Resultado: ...