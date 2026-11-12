# Ruta: src/centros_de_trabajo/politicas_ct/horno/mock_horno.py en PC LAB
import time
from centros_de_trabajo.politicas_ct.horno.modelo import CurvaHorno


class MockHorno:
    """Horno falso para MVP sin hardware. Simula tiempo con el reloj."""

    def __init__(self) -> None:
        self._curva_en_curso: CurvaHorno | None = None
        self._timestamp_inicio: float | None = None
        self._abortado: bool = False

    def iniciar_curva(self, curva_a_ejecutar: CurvaHorno) -> list[str]:
        errores_validacion = curva_a_ejecutar.validar()
        if errores_validacion:
            return errores_validacion
        self._curva_en_curso = curva_a_ejecutar
        self._timestamp_inicio = time.time()
        self._abortado = False
        return []

    def abortar(self) -> None:
        self._abortado = True
        self._curva_en_curso = None
        self._timestamp_inicio = None

    def esta_en_marcha(self) -> bool:
        return self._curva_en_curso is not None and not self._abortado

    def leer_temperatura_actual(self) -> float:
        if not self.esta_en_marcha():
            return 20.0
        assert self._timestamp_inicio is not None
        assert self._curva_en_curso is not None
        segundos_transcurridos = time.time() - self._timestamp_inicio
        # Mock coherente, no físicamente correcto: sube 1 grado por segundo
        # hasta el objetivo de rampa, después se queda.
        objetivo = self._curva_en_curso.rampa.temperatura_objetivo
        return min(20.0 + segundos_transcurridos, float(objetivo))

    def tiempo_operacion_minutos(self) -> float:
        if self._timestamp_inicio is None:
            return 0.0
        return (time.time() - self._timestamp_inicio) / 60.0