import xmlrpc.client
from pathlib import Path
from xml.parsers.expat import ExpatError

from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden


class ErrorDeLogin(Exception):
    """Odoo respondió, pero no aceptó base + usuario + clave."""


def _proxy(url: str, ruta: str, timeout: float) -> xmlrpc.client.ServerProxy:
    """ServerProxy con timeout (por defecto xmlrpc no tiene ninguno)."""
    base = xmlrpc.client.SafeTransport if url.startswith("https") else xmlrpc.client.Transport

    class _Transporte(base):
        def make_connection(self, host):
            conexion = super().make_connection(host)
            conexion.timeout = timeout
            return conexion

    return xmlrpc.client.ServerProxy(f"{url}{ruta}", transport=_Transporte())


class OdooBackend:
    def __init__(self, url: str, db: str, user: str, key_file: Path, timeout: float = 10) -> None:
        self._url, self._db, self._user = url, db, user
        self._key_file, self._timeout = key_file, timeout
        self._uid: int | None = None
        self._clave: str | None = None

    def _autenticar(self) -> None:
        if self._uid:
            return
        self._clave = self._key_file.read_text().strip()
        common = _proxy(self._url, "/xmlrpc/2/common", self._timeout)
        uid = common.authenticate(self._db, self._user, self._clave, {})
        if not uid:
            raise ErrorDeLogin("usuario, base o clave incorrectos")
        self._uid = uid

    def verificar(self) -> Resultado:
        """Lectura inocua del propio usuario: prueba de conexión."""
        return self._con_manejo_de_errores(self._leer_usuario)

    def _leer_usuario(self) -> Resultado:
        self._autenticar()
        modelos = _proxy(self._url, "/xmlrpc/2/object", self._timeout)
        datos = modelos.execute_kw(self._db, self._uid, self._clave, "res.users", "read",
                                   [[self._uid]], {"fields": ["name"]})
        return Resultado(True, f"Conectado como {datos[0]['name']}")

    def enviar(self, orden: Orden) -> Resultado:
        # PENDIENTE: definir qué es un "proceso" en Odoo (¿mrp.workorder?).
        # Por ahora solo comprueba que la conexión funciona, no modifica nada.
        def accion() -> Resultado:
            self._autenticar()
            return Resultado(True, f"{orden.value}: conexión OK, el mapeo a Odoo está pendiente")

        return self._con_manejo_de_errores(accion)

    def _con_manejo_de_errores(self, accion) -> Resultado:
        try:
            return accion()
        except FileNotFoundError:
            return Resultado(False, f"No existe la clave en {self._key_file}")
        except ErrorDeLogin as e:
            return Resultado(False, str(e))
        except xmlrpc.client.Fault as e:
            return Resultado(False, f"Odoo rechazó el pedido: {e.faultString[:120]}")
        except xmlrpc.client.ProtocolError as e:
            return Resultado(False, f"HTTP {e.errcode}")
        except (ExpatError, OSError) as e:
            return Resultado(False, f"Sin respuesta válida de Odoo: {e}")