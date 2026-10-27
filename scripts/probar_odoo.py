"""Prueba de conexión a Odoo por capas: red -> clave -> login -> lectura."""
import socket
import sys
import xmlrpc.client
from pathlib import Path
from xml.parsers.expat import ExpatError

URL = "https://torneria.dynamicity.com.ar"   # sin ruta y sin "/" final
DB = "torneria_db"
USER = "operador@gmail.com"
KEY_FILE = Path("/var/lib/centro-trabajo/odoo.key")
TIMEOUT = 10


def fallar(capa: str, detalle: str) -> None:
    print(f"[FALLA] {capa}: {detalle}")
    sys.exit(1)


def main() -> None:
    socket.setdefaulttimeout(TIMEOUT)

    # Capa 1: ¿llego al servidor y responde XML-RPC?
    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    try:
        version = common.version()
    except xmlrpc.client.ProtocolError as e:
        fallar("1-red", f"HTTP {e.errcode} (¿Cloudflare o proxy bloqueando /xmlrpc?)")
    except ExpatError:
        fallar("1-red", "respondió algo que no es XML (¿página HTML de Cloudflare?)")
    except OSError as e:
        fallar("1-red", f"sin conexión: {e}")
    print(f"[OK] 1-red: Odoo {version.get('server_version')}")

    # Capa 2: ¿existe y se puede leer la clave?
    if not KEY_FILE.is_file():
        fallar("2-clave", f"no existe {KEY_FILE}")
    clave = KEY_FILE.read_text().strip()
    print("[OK] 2-clave: archivo leído")

    # Capa 3: ¿Odoo acepta usuario + clave en esa base?
    try:
        uid = common.authenticate(DB, USER, clave, {})
    except xmlrpc.client.Fault as e:
        fallar("3-login", f"Odoo respondió un error (¿base inexistente?): {e.faultString[:200]}")
    if not uid:
        fallar("3-login", "usuario o clave incorrectos")
    print(f"[OK] 3-login: uid={uid}")

    # Capa 4: lectura inocua de tu propio usuario
    modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")
    datos = modelos.execute_kw(DB, uid, clave, "res.users", "read", [[uid]], {"fields": ["name", "login"]})
    print(f"[OK] 4-lectura: {datos[0]}")


if __name__ == "__main__":
    main()