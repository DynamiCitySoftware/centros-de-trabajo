"""Prueba de escrituras sobre UNA orden de trabajo. MODIFICA DATOS REALES."""
import sys
import xmlrpc.client

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
LOGIN = "operador@gmail.com"
RUTA_CLAVE = "/var/lib/centro-trabajo/odoo.key"

ACCIONES = {
    "iniciar": "button_start",
    "reanudar": "button_start",
    "pausar": "button_pending",
    "terminar": "button_finish",
}

clave = open(RUTA_CLAVE).read().strip()
uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, LOGIN, clave, {})
modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def ejecutar(modelo, metodo, args, kwargs=None):
    return modelos.execute_kw(DB, uid, clave, modelo, metodo, args, kwargs or {})


def mostrar(titulo, wo_id):
    wo = ejecutar("mrp.workorder", "read", [[wo_id]],
                  {"fields": ["name", "state", "is_user_working", "working_user_ids", "duration"]})[0]
    abiertos = ejecutar("mrp.workcenter.productivity", "search_read",
                        [[("workorder_id", "=", wo_id), ("date_end", "=", False)]],
                        {"fields": ["user_id", "date_start"]})
    print(f"--- {titulo} ---")
    print(wo)
    print("cronómetros abiertos:", abiertos)


def main() -> None:
    if len(sys.argv) != 3 or sys.argv[2] not in ACCIONES:
        sys.exit(f"Uso: probar_escrituras.py <id_wo> <{'|'.join(ACCIONES)}>")
    wo_id = int(sys.argv[1])   # id de la WO de prueba (valor genérico: el que muestre explorar_ordenes.py)
    accion = sys.argv[2]

    mostrar("ANTES", wo_id)
    try:
        retorno = ejecutar("mrp.workorder", ACCIONES[accion], [[wo_id]])
        print(f">>> {accion}: Odoo devolvió {retorno!r}")
    except xmlrpc.client.Fault as e:
        print(f">>> {accion}: Fault de Odoo: {e.faultString[-300:]}")
    mostrar("DESPUÉS", wo_id)


if __name__ == "__main__":
    main()