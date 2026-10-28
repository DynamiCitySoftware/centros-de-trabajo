"""Explora modelos de Odoo por XML-RPC. Solo lee, no modifica nada."""
import sys
import xmlrpc.client
from pathlib import Path

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
USER = "operador@gmail.com"
KEY_FILE = Path("/var/lib/centro-trabajo/odoo.key")


def conectar():
    clave = KEY_FILE.read_text().strip()
    uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, USER, clave, {})
    modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    def llamar(modelo, metodo, args, kwargs=None):
        return modelos.execute_kw(DB, uid, clave, modelo, metodo, args, kwargs or {})

    return llamar


def main() -> None:
    llamar = conectar()
    filtro = sys.argv[1] if len(sys.argv) > 1 else "mrp."

    if len(sys.argv) > 2:
        # Con un segundo argumento: campos de ese modelo exacto
        campos = llamar(sys.argv[2], "fields_get", [], {"attributes": ["string", "type", "selection"]})
        for nombre, info in sorted(campos.items()):
            extra = f"  {info['selection']}" if info.get("selection") else ""
            print(f"{nombre:35} {info['type']:12} {info['string']}{extra}")
        return

    # Solo un argumento: lista los modelos cuyo nombre empieza con ese texto
    for m in llamar("ir.model", "search_read", [[("model", "=like", f"{filtro}%")]], {"fields": ["model", "name"]}):
        print(f"{m['model']:35} {m['name']}")


if __name__ == "__main__":
    main()