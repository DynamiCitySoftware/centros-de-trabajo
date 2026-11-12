import xmlrpc.client
from pathlib import Path
from xml.parsers.expat import ExpatError

from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo

# Texto fijo del error de Python cuando un botón de Odoo devuelve None y el
# servidor no puede serializarlo. Medido: la acción SÍ se ejecutó.
MSG_RETORNO_NONE = "cannot marshal None"

# Medido en scripts/probar_escrituras.py
BOTON_POR_ORDEN = {
    Orden.INICIAR: "button_start",
    Orden.TERMINAR: "button_finish",
}

CAMPOS_WO = ["name", "state", "is_user_working", "working_state", "working_user_ids"]

TAMANO_PAGINA_LISTADO = 200

CAMPOS_LISTADO_WO = [
    "id",
    "name",
    "state",
    "is_user_working",
    "working_state",
    "working_user_ids",
]


class ErrorDeLogin(Exception):
    """Odoo respondió, pero no aceptó base + usuario + clave."""


class OrdenNoExiste(Exception):
    """No hay una mrp.workorder con ese id (read devuelve [])."""


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
        self._modelos: xmlrpc.client.ServerProxy | None = None

    def _autenticar(self) -> None:
        if self._uid:
            return
        self._clave = self._key_file.read_text().strip()
        common = _proxy(self._url, "/xmlrpc/2/common", self._timeout)
        uid = common.authenticate(self._db, self._user, self._clave, {})
        if not uid:
            raise ErrorDeLogin("usuario, base o clave incorrectos")
        self._uid = uid

    def _ejecutar(self, modelo: str, metodo: str, args: list, kwargs: dict | None = None):
        """Único punto por donde sale una llamada a Odoo (los tests lo reemplazan)."""
        self._autenticar()
        if self._modelos is None:
            self._modelos = _proxy(self._url, "/xmlrpc/2/object", self._timeout)
        return self._modelos.execute_kw(self._db, self._uid, self._clave,
                                        modelo, metodo, args, kwargs or {})

    def verificar(self) -> Resultado:
        """Lectura inocua del propio usuario: prueba de conexión."""
        return self._con_manejo_de_errores(self._leer_usuario)

    def _leer_usuario(self) -> Resultado:
        datos = self._ejecutar("res.users", "read", [[self._uid or 0]], {"fields": ["name"]}) \
            if self._uid else None
        if datos is None:
            self._autenticar()
            datos = self._ejecutar("res.users", "read", [[self._uid]], {"fields": ["name"]})
        return Resultado(True, f"Conectado como {datos[0]['name']}")

    def leer_orden(self, id_orden: int) -> OrdenDeTrabajo:
        """Lee la WO desde Odoo. Lanza OrdenNoExiste si no está."""
        datos = self._ejecutar("mrp.workorder", "read", [[id_orden]], {"fields": CAMPOS_WO})
        if not datos:
            raise OrdenNoExiste(f"No existe la orden de trabajo {id_orden}")
        return OrdenDeTrabajo.desde_odoo(datos[0], self._uid)

    def _llamar_boton(self, metodo: str, id_orden: int) -> None:
        """Ejecuta un botón de mrp.workorder. Solo tolera el Fault de retorno None."""
        try:
            self._ejecutar("mrp.workorder", metodo, [[id_orden]])
        except xmlrpc.client.Fault as e:
            if MSG_RETORNO_NONE in e.faultString:
                return
            raise

    def enviar(self, orden: Orden, id_orden: int) -> Resultado:
        return self._con_manejo_de_errores(lambda: self._enviar(orden, id_orden))

    def _enviar(self, orden: Orden, id_orden: int) -> Resultado:
        # 1) Leer: Odoo es la fuente de verdad, no un estado guardado acá.
        antes = self.leer_orden(id_orden)
        estado = derivar_estado(antes)
        # 2) Validar ANTES de escribir.
        if not puede(estado, orden):
            return Resultado(False, f"{orden.value} no es válida: la orden está {estado.value}")
        # 3) Escribir.
        self._llamar_boton(BOTON_POR_ORDEN[orden], id_orden)
        # 4) Verificar leyendo de nuevo: no se confía en la respuesta del botón.
        despues = self.leer_orden(id_orden)
        if not cumple_postcondicion(orden, despues):
            return Resultado(False, f"Odoo no reflejó '{orden.value}': "
                                    f"ahora está {derivar_estado(despues).value}")
        return Resultado(True, f"{orden.value} aplicada ({derivar_estado(despues).value})")

    def _con_manejo_de_errores(self, accion) -> Resultado:
        try:
            return accion()
        except FileNotFoundError:
            return Resultado(False, f"No existe la clave en {self._key_file}")
        except ErrorDeLogin as e:
            return Resultado(False, str(e))
        except OrdenNoExiste as e:
            return Resultado(False, str(e))
        except ValueError as e:
            return Resultado(False, str(e))
        except xmlrpc.client.Fault as e:
            return Resultado(False, f"Odoo rechazó el pedido: {e.faultString[:120]}")
        except xmlrpc.client.ProtocolError as e:
            return Resultado(False, f"HTTP {e.errcode}")
        except (ExpatError, OSError) as e:
            return Resultado(False, f"Sin respuesta válida de Odoo: {e}")
    
    def listar_ordenes(self) -> list[OrdenDeTrabajo]:
        """Lista todas las WO ready/done, las asignadas al usuario
        y aquellas en las que tiene o tuvo registros de tiempo.
        """
        self._autenticar()
        uid = self._uid

        dominio = [
            "|", "|", "|",
            ("state", "=", "ready"),
            ("state", "=", "done"),
            ("production_id.user_id", "=", uid),
            ("time_ids.user_id", "=", uid),
        ]

        registros_por_id = {}
        offset = 0

        while True:
            pagina = self._ejecutar(
                "mrp.workorder",
                "search_read",
                [dominio],
                {
                    "fields": CAMPOS_LISTADO_WO,
                    "limit": TAMANO_PAGINA_LISTADO,
                    "offset": offset,
                    "order": "id asc",
                },
            )

            if not pagina:
                break

            for registro in pagina:
                registros_por_id[registro["id"]] = registro

            if len(pagina) < TAMANO_PAGINA_LISTADO:
                break

            offset += len(pagina)

        return [
            OrdenDeTrabajo.desde_odoo(registro, uid)
            for registro in registros_por_id.values()
        ]