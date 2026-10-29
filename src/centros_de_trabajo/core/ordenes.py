from dataclasses import dataclass
from enum import Enum


class Orden(Enum):
    """Los 4 comandos que el kiosco puede enviar."""
    INICIAR = "iniciar"
    PAUSAR = "pausar"
    REANUDAR = "reanudar"
    TERMINAR = "terminar"


@dataclass(frozen=True)
class OrdenDeTrabajo:
    """Una orden de trabajo tal como la informa Odoo (modelo mrp.workorder).

    Solo guarda datos, no decide nada. frozen=True: una vez creada no se modifica,
    así nadie la "corrige" por su cuenta y se desvía de lo que dijo Odoo.
    """
    id: int
    nombre: str
    state: str                  # valor crudo de Odoo: pending/waiting/ready/progress/done/cancel
    is_user_working: bool       # ¿el usuario que consulta tiene el cronómetro abierto?
    working_state: str          # estado del centro de trabajo: normal / blocked / done
    otros_trabajando: bool = False  # ¿hay otro usuario con el cronómetro abierto?

    @classmethod
    def desde_odoo(cls, registro: dict, uid: int) -> "OrdenDeTrabajo":
        """registro: un dict de search_read con id, name, state, is_user_working,
        working_state y working_user_ids. uid: el id del usuario logueado."""
        otros = [u for u in registro.get("working_user_ids", []) if u != uid]
        return cls(
            id=registro["id"],
            nombre=registro["name"],
            state=registro["state"],
            is_user_working=bool(registro["is_user_working"]),
            working_state=registro["working_state"],
            otros_trabajando=bool(otros),
        )