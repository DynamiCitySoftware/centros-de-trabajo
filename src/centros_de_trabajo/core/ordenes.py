from enum import Enum


class Orden(Enum):
    INICIAR = "iniciar"
    PAUSAR = "pausar"
    REANUDAR = "reanudar"
    TERMINAR = "terminar"