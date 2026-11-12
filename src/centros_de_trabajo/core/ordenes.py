# Ruta: src/centros_de_trabajo/core/ordenes.py en PC LAB
from dataclasses import dataclass
from enum import Enum


class Orden(Enum):
    INICIAR = "iniciar"
    TERMINAR = "terminar"
    ABORTAR = "abortar"


@dataclass(frozen=True)
class OrdenDeTrabajo:
    id_odoo: int
    operacion_nombre: str  # ej: "horneado simple", viene de WO['name']
    estado_odoo: str  # ej: "ready", "progress", "done", "cancel"
    workcenter_nombre: str  # ej: "Horno Microondas", viene de WO['workcenter_id'][1]
    usuario_es_responsable: bool
    existe_cronometro_para_usuario: bool
    duracion_minutos: float  # mapea WO['duration'], es tiempo_proceso sum(time_ids)

    @classmethod
    def desde_odoo(
        cls,
        registro_odoo: dict,
        uid_actual: int,
        id_responsable_produccion: int | None = None,
    ) -> "OrdenDeTrabajo":
        working_ids = registro_odoo.get("working_user_ids") or []
        return cls(
            id_odoo=registro_odoo["id"],
            operacion_nombre=registro_odoo.get("name") or "",
            estado_odoo=registro_odoo.get("state") or "",
            workcenter_nombre=(registro_odoo.get("workcenter_id") or ["", ""])[1] or "",
            usuario_es_responsable=(
                id_responsable_produccion == uid_actual
                if id_responsable_produccion is not None else False
            ),
            existe_cronometro_para_usuario=uid_actual in working_ids,
            duracion_minutos=float(registro_odoo.get("duration") or 0.0),
        )