"""Explora candidatos para listar_ordenes(). Solo lee, no modifica nada.

Uso desde la raíz del repo, dentro de nix develop:
    python3 scripts/explorar_listado_ordenes.py <usuario> <ruta_clave>
"""
import argparse
import xmlrpc.client
from pathlib import Path

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"

CAMPOS = ["name", "state", "production_id", "production_state",
          "workcenter_id", "is_user_working", "working_user_ids"]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("usuario", help="login real del usuario de Odoo, esto es un valor generico")
    ap.add_argument("ruta_clave", type=Path, help="archivo con solo su API key, esto es un valor generico")
    args = ap.parse_args()

    clave = args.ruta_clave.read_text().strip()
    uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, args.usuario, clave, {})
    modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    def ejecutar(modelo, metodo, dominio, kwargs=None):
        return modelos.execute_kw(DB, uid, clave, modelo, metodo, [dominio], kwargs or {})

    print(f"uid autenticado: {uid}")

    dom_responsable = [("production_id.user_id", "=", uid)]
    dom_trabajadas = [("time_ids.user_id", "=", uid)]
    dom_combinado = ["|"] + dom_responsable + dom_trabajadas

    for nombre, dominio in [
        ("A_responsable", dom_responsable),
        ("B_trabajadas", dom_trabajadas),
        ("C_combinado", dom_combinado),
    ]:
        try:
            filas = ejecutar("mrp.workorder", "search_read", dominio, {"fields": CAMPOS, "limit": 20})
            print(f"\n--- {nombre}: {len(filas)} ---")
            for f in filas:
                print(f)
        except xmlrpc.client.Fault as e:
            print(f"\n--- {nombre}: FAULT ---")
            print(e.faultString[-500:])


if __name__ == "__main__":
    main()