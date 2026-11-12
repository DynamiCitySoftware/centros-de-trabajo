# Ruta: src/centros_de_trabajo/politicas_ct/horno/modelo.py en PC LAB
from dataclasses import dataclass


POTENCIA_MAXIMA_GENERICA = 800  # VALOR GENERICO, reemplazar por watts reales del microondas doméstico


@dataclass(frozen=True)
class PasoHorno:
    temperatura_objetivo: float
    potencia: int


@dataclass(frozen=True)
class CurvaHorno:
    rampa: PasoHorno    
    enfriamiento: PasoHorno | None = None
    meseta_temperatura: float | None = None
    meseta_tiempo_minutos: float | None = None

    def validar(self) -> list[str]:
        errores: list[str] = []
        if self.rampa.potencia <= 0 or self.rampa.potencia > POTENCIA_MAXIMA_GENERICA:
            errores.append("rampa.potencia fuera de rango")
        if self.enfriamiento is None:
            errores.append("enfriamiento es obligatorio")
        elif self.enfriamiento.potencia < 0 or self.enfriamiento.potencia > POTENCIA_MAXIMA_GENERICA:
            errores.append("enfriamiento.potencia fuera de rango")
        hay_meseta_temp = self.meseta_temperatura is not None
        hay_meseta_tiempo = self.meseta_tiempo_minutos is not None
        if hay_meseta_temp != hay_meseta_tiempo:
            errores.append("meseta incompleta: temperatura y tiempo van juntos")
        return errores

    def es_valida(self) -> bool:
        return self.validar() == []