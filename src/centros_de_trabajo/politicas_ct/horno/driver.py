# Ruta: src/centros_de_trabajo/politicas_ct/horno/driver.py en PC LAB
import abc
from centros_de_trabajo.politicas_ct.horno.modelo import CurvaHorno


class HornoDriver(abc.ABC):
    """Contrato que todo horno debe cumplir, mock o serie/USB."""

    @abc.abstractmethod
    def iniciar_curva(self, curva_a_ejecutar: CurvaHorno) -> list[str]:
        """Devuelve [] si arranca, o lista de errores si la curva es inválida."""
        ...

    @abc.abstractmethod
    def leer_temperatura_actual(self) -> float:
        ...

    @abc.abstractmethod
    def esta_en_marcha(self) -> bool:
        ...

    @abc.abstractmethod
    def detener(self) -> None:
        """Parada de bajo nivel. No es orden de kiosco, no pasa por Odoo."""
        ...


class DriverSerieUSB(HornoDriver):
    """Driver real pensado para puerto serie/USB. Tu colega lo completa.

    Protocolo inicial coherente, no definitivo:
      PC -> HORNO: "RAMPA <temp> <pot>\n"
      PC -> HORNO: "MESETA <temp> <min>\n" (solo si hay meseta)
      PC -> HORNO: "ENFRIAR <temp> <pot>\n"
      PC -> HORNO: "DETENER\n"
      HORNO -> PC: "TEMP <valor>\n" / "OK\n" / "ERR <motivo>\n"
    """

    def __init__(self, puerto: str = "/dev/ttyUSB0", baudios: int = 115200) -> None:
        # VALOR GENERICO puerto y baudios, reemplazar por los reales del microondas.
        self._puerto_nombre = puerto
        self._baudios = baudios
        self._puerto = None
        self._en_marcha = False

    def _abrir_si_cerrado(self) -> None:
        if self._puerto is not None:
            return
        # Import diferido para que los tests sin pyserial sigan pasando.
        import serial  # dependencia: pyserial en PC LAB
        self._puerto = serial.Serial(self._puerto_nombre, self._baudios, timeout=2)

    def _enviar_linea(self, linea: str) -> str:
        self._abrir_si_cerrado()
        assert self._puerto is not None
        self._puerto.write((linea + "\n").encode("ascii"))
        respuesta = self._puerto.readline().decode("ascii", errors="replace").strip()
        return respuesta

    def iniciar_curva(self, curva_a_ejecutar: CurvaHorno) -> list[str]:
        errores = curva_a_ejecutar.validar()
        if errores:
            return errores
        try:
            self._enviar_linea(f"RAMPA {curva_a_ejecutar.rampa.temperatura_objetivo} {curva_a_ejecutar.rampa.potencia}")
            if curva_a_ejecutar.meseta_temperatura is not None:
                self._enviar_linea(f"MESETA {curva_a_ejecutar.meseta_temperatura} {curva_a_ejecutar.meseta_tiempo_minutos}")
            assert curva_a_ejecutar.enfriamiento is not None
            self._enviar_linea(f"ENFRIAR {curva_a_ejecutar.enfriamiento.temperatura_objetivo} {curva_a_ejecutar.enfriamiento.potencia}")
        except Exception as e:
            return [f"serie/USB no responde en {self._puerto_nombre}: {e}"]
        self._en_marcha = True
        return []

    def leer_temperatura_actual(self) -> float:
        try:
            respuesta = self._enviar_linea("TEMP?")
            # Espera "TEMP <valor>", si no se puede parsear devuelve 20.0 coherente.
            partes = respuesta.split()
            if len(partes) == 2 and partes[0] == "TEMP":
                return float(partes[1].replace(",", "."))
        except Exception:
            pass
        return 20.0

    def esta_en_marcha(self) -> bool:
        return self._en_marcha

    def detener(self) -> None:
        try:
            self._enviar_linea("DETENER")
        finally:
            self._en_marcha = False
            if self._puerto is not None:
                try:
                    self._puerto.close()
                finally:
                    self._puerto = None