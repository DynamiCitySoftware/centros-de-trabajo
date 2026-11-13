# Ruta: src/centros_de_trabajo/backends/odoo.py en PC LAB - reemplazar TODO el archivo
import traceback
import xmlrpc.client
from pathlib import Path
from xml.parsers.expat import ExpatError
import json

from centros_de_trabajo.backends.base import Resultado
from centros_de_trabajo.core.ordenes import Orden, OrdenDeTrabajo

MSG_RETORNO_NONE = "cannot marshal None"

BOTON_POR_ORDEN = {
    Orden.INICIAR: "button_start",
    Orden.TERMINAR: "button_finish",
}

CAMPOS_WO = ["name", "state", "is_user_working", "working_state", "working_user_ids",
             "workcenter_id", "duration"]
TAMANO_PAGINA_LISTADO = 200
CAMPOS_LISTADO_WO = ["id", "name", "state", "is_user_working", "working_state",
                     "working_user_ids", "workcenter_id", "duration"]


class ErrorDeLogin(Exception):
    pass


class OrdenNoExiste(Exception):
    pass


def _proxy(url: str, ruta: str, timeout: float) -> xmlrpc.client.ServerProxy:
    base = xmlrpc.client.SafeTransport if url.startswith("https") else xmlrpc.client.Transport

    class _Transporte(base):  # type: ignore
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
        self._cliente_proxy_modelos: xmlrpc.client.ServerProxy | None = None

    def _autenticar(self) -> None:
        if self._uid:
            return
        print(f"[odoo] autenticando user={self._user} db={self._db}", flush=True)
        self._clave = self._key_file.read_text().strip()
        comun = _proxy(self._url, "/xmlrpc/2/common", self._timeout)
        uid = comun.authenticate(self._db, self._user, self._clave, {})
        if not uid:
            raise ErrorDeLogin("usuario, base o clave incorrectos")
        self._uid = uid
        print(f"[odoo] autenticado uid={self._uid}", flush=True)

    def _ejecutar(self, modelo: str, metodo: str, args: list, kwargs: dict | None = None):
        self._autenticar()
        if self._cliente_proxy_modelos is None:
            self._cliente_proxy_modelos = _proxy(self._url, "/xmlrpc/2/object", self._timeout)
        print(f"[odoo] exec {modelo}.{metodo} args={args} kwargs={kwargs}", flush=True)
        try:
            ret = self._cliente_proxy_modelos.execute_kw(self._db, self._uid, self._clave, modelo, metodo, args, kwargs or {})
            print(f"[odoo] ok {modelo}.{metodo} tipo_ret={type(ret).__name__}", flush=True)
            return ret
        except Exception as e:
            print(f"[odoo] EXCEPCION en {modelo}.{metodo}: {e}", flush=True)
            traceback.print_exc()
            raise

    def verificar(self) -> Resultado:
        return self._con_manejo_de_errores(self._leer_usuario)

    def _leer_usuario(self) -> Resultado:
        print("[odoo] verificar: leyendo res.users", flush=True)
        datos = self._ejecutar("res.users", "read", [[self._uid or 0]], {"fields": ["name"]})
        print(f"[odoo] verificar ret={datos}", flush=True)
        return Resultado(True, f"Conectado como {datos[0]['name']}")

    def leer_orden(self, id_orden: int) -> OrdenDeTrabajo:
        print(f"[odoo] leer_orden id={id_orden}", flush=True)
        datos = self._ejecutar("mrp.workorder", "read", [[id_orden]], {"fields": CAMPOS_WO})
        if not datos:
            raise OrdenNoExiste(f"No existe la orden de trabajo {id_orden}")
        print(f"[odoo] leer_orden raw={datos[0]}", flush=True)
        return OrdenDeTrabajo.desde_odoo(datos[0], self._uid)

    def _llamar_boton(self, metodo: str, id_orden: int) -> None:
        print(f"[odoo] boton {metodo} sobre WO {id_orden}", flush=True)
        try:
            self._ejecutar("mrp.workorder", metodo, [[id_orden]])
            print(f"[odoo] boton {metodo} WO {id_orden} sin fault", flush=True)
        except xmlrpc.client.Fault as e:
            print(f"[odoo] fault en {metodo}: {e.faultString[:300]}", flush=True)
            if MSG_RETORNO_NONE in e.faultString:
                print("[odoo] fault es retorno None, se tolera", flush=True)
                return
            raise

    def enviar(self, orden: Orden, id_orden: int) -> Resultado:
        return self._con_manejo_de_errores(lambda: self._enviar(orden, id_orden))

    def _enviar(self, orden: Orden, id_orden: int) -> Resultado:
        print(f"[odoo] _enviar orden={orden.value} id={id_orden}", flush=True)
        antes = self.leer_orden(id_orden)
        print(f"[odoo] estado antes={antes.estado_odoo}", flush=True)
        metodo = BOTON_POR_ORDEN.get(orden)
        if metodo is None:
            return Resultado(False, f"{orden.value} no soportada por OdooBackend.")
        self._llamar_boton(metodo, id_orden)
        print("[odoo] releyendo después de botón", flush=True)
        despues = self.leer_orden(id_orden)
        print(f"[odoo] estado despues={despues.estado_odoo}", flush=True)
        return Resultado(True, f"{orden.value} aplicada ({antes.estado_odoo} -> {despues.estado_odoo})")

    def _con_manejo_de_errores(self, accion) -> Resultado:
        try:
            return accion()
        except FileNotFoundError:
            print(f"[odoo] no existe clave en {self._key_file}", flush=True)
            return Resultado(False, f"No existe la clave en {self._key_file}")
        except ErrorDeLogin as e:
            print(f"[odoo] login fail: {e}", flush=True)
            return Resultado(False, str(e))
        except OrdenNoExiste as e:
            print(f"[odoo] {e}", flush=True)
            return Resultado(False, str(e))
        except xmlrpc.client.Fault as e:
            print(f"[odoo] Fault: {e.faultString[:300]}", flush=True)
            return Resultado(False, f"Odoo rechazó el pedido: {e.faultString[:120]}")
        except xmlrpc.client.ProtocolError as e:
            print(f"[odoo] ProtocolError {e.errcode}", flush=True)
            return Resultado(False, f"HTTP {e.errcode}")
        except (ExpatError, OSError) as e:
            print(f"[odoo] red/expat: {e}", flush=True)
            traceback.print_exc()
            return Resultado(False, f"Sin respuesta válida de Odoo: {e}")

    def listar_ordenes(self) -> list[OrdenDeTrabajo]:
        print("[odoo] listar_ordenes inicio", flush=True)
        self._autenticar()
        uid = self._uid
        dominio = [("state", "in", ["ready", "progress", "done"])]
        registros_por_id = {}
        offset = 0
        while True:
            pagina = self._ejecutar("mrp.workorder", "search_read", [dominio],
                {"fields": CAMPOS_LISTADO_WO, "limit": TAMANO_PAGINA_LISTADO, "offset": offset, "order": "id asc"})
            print(f"[odoo] pagina offset={offset} n={len(pagina)}", flush=True)
            if not pagina:
                break
            for registro in pagina:
                registros_por_id[registro["id"]] = registro
            if len(pagina) < TAMANO_PAGINA_LISTADO:
                break
            offset += len(pagina)
        print(f"[odoo] listar_ordenes total={len(registros_por_id)}", flush=True)
        return [OrdenDeTrabajo.desde_odoo(r, uid) for r in registros_por_id.values()]
    

    def publicar_curva_en_chatter(self, id_orden: int, curva) -> Resultado:
        cuerpo = f"Curva horno: {json.dumps({'rampa': [curva.rampa.temperatura_objetivo, curva.rampa.potencia], 'meseta_temp': curva.meseta_temperatura, 'meseta_min': curva.meseta_tiempo_minutos, 'enf': [curva.enfriamiento.temperatura_objetivo, curva.enfriamiento.potencia]}, ensure_ascii=False)}"
        return self._con_manejo_de_errores(lambda: Resultado(True, str(self._ejecutar("mrp.workorder", "message_post", [[id_orden]], {"body": cuerpo, "message_type": "comment"}))))