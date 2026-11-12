# Ruta: src/centros_de_trabajo/workcenters/base.py en PC LAB
import abc
import enum
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo

class EstadoKiosco(enum.Enum):
    DETENIDO = "detenido"
    EN_CURSO = "en_curso"
    TERMINADO = "terminado"
    ABORTADO = "abortado"
    NO_DISPONIBLE = "no_disponible"


class Orden(enum.Enum):
    INICIAR = "iniciar"
    TERMINAR = "terminar"
    ABORTAR = "abortar"


class CentroDeTrabajo(abc.ABC):
    nombre_odoo: str = ""
    operaciones_soportadas: list[str] = []

    def es_mia(self, ot: OrdenDeTrabajo) -> bool:
        return (
            ot.workcenter_nombre == self.nombre_odoo
            and ot.operacion_nombre in self.operaciones_soportadas
        )

    @abc.abstractmethod
    def derivar_estado(self, ot: OrdenDeTrabajo) -> EstadoKiosco:
        ...

    @abc.abstractmethod
    def ordenes_validas(self, estado: EstadoKiosco) -> set[Orden]:
        ...