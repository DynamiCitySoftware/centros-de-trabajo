"""Prueba de escrituras sobre UNA orden de trabajo (mrp.workorder).
MODIFICA DATOS REALES en Odoo: usar solo una WO de prueba.

Uso:
    python3 scripts/probar_escrituras.py <id_wo> <iniciar|reanudar|pausar|terminar>
    python3 scripts/probar_escrituras.py <id_wo> secuencia
"""
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

# Texto fijo del error de Python cuando Odoo devuelve None y el servidor
# no puede serializarlo. La acción ya se ejecutó cuando esto ocurre.
MSG_RETORNO_NONE = "cannot marshal None"

# (acción, ¿esperamos que Odoo la rechace?)
SECUENCIA = [
    ("iniciar", False),
    ("iniciar", False),
    ("pausar", False),
    ("pausar", False),
    ("reanudar", False),
    ("pausar", False),
    ("terminar", False),
    ("iniciar", True),   # sobre una WO terminada: Odoo debe rechazarla
]

# Estado esperado de la WO DESPUÉS de cada acción (si no se espera rechazo)
ESPERADO = {
    "iniciar": {"state": "progress", "is_user_working": True},
    "reanudar": {"state": "progress", "is_user_working": True},
    "pausar": {"state": "progress", "is_user_working": False},
    "terminar": {"state": "done", "is_user_working": False},
}

CAMPOS = ["name", "state", "is_user_working", "working_user_ids", "duration",
          "production_id", "production_state"]

clave = open(RUTA_CLAVE).read().strip()
uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, LOGIN, clave, {})
if not uid:
    sys.exit("Autenticación fallida (revisá DB, login y clave).")
modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def ejecutar(modelo, metodo, args, kwargs=None):
    return modelos.execute_kw(DB, uid, clave, modelo, metodo, args, kwargs or {})


def leer_orden(wo_id):
    """Devuelve el dict de la WO, o None si no existe (read devuelve [])."""
    datos = ejecutar("mrp.workorder", "read", [[wo_id]], {"fields": CAMPOS})
    return datos[0] if datos else None


def mostrar(titulo, wo_id):
    wo = leer_orden(wo_id)
    abiertos = ejecutar("mrp.workcenter.productivity", "search_read",
                        [[("workorder_id", "=", wo_id), ("date_end", "=", False)]],
                        {"fields": ["user_id", "date_start"]})
    print(f"--- {titulo} ---")
    print(wo)
    print("cronómetros abiertos:", abiertos)
    return wo


def llamar_boton(metodo, wo_id):
    """Ejecuta un botón de mrp.workorder. Devuelve (veredicto, detalle).

    OK                    -> Odoo respondió normalmente.
    NONE_NO_SERIALIZABLE  -> el botón devolvió None y el servidor no pudo
                             armar la respuesta. NO prueba que haya funcionado:
                             se verifica leyendo el estado después.
    FAULT                 -> error real de Odoo (cualquier otro Fault).
    """
    try:
        retorno = ejecutar("mrp.workorder", metodo, [[wo_id]])
        return "OK", f"Odoo devolvió {retorno!r}"
    except xmlrpc.client.Fault as e:
        if MSG_RETORNO_NONE in e.faultString:
            return "NONE_NO_SERIALIZABLE", "el botón devolvió None (se verifica leyendo)"
        return "FAULT", e.faultString[-300:]


def ejecutar_paso(wo_id, accion, espera_rechazo=False):
    """Un paso: ANTES, botón, DESPUÉS y comparación. Devuelve True si coincide."""
    antes = mostrar("ANTES", wo_id)
    veredicto, detalle = llamar_boton(ACCIONES[accion], wo_id)
    print(f">>> {accion}: {veredicto} | {detalle}")
    despues = mostrar("DESPUÉS", wo_id)

    if espera_rechazo:
        # Un rechazo no debe cambiar nada
        esperado = {k: antes[k] for k in ("state", "is_user_working")}
        veredicto_ok = veredicto == "FAULT"
    else:
        esperado = ESPERADO[accion]
        veredicto_ok = veredicto != "FAULT"

    estado_ok = all(despues[k] == v for k, v in esperado.items())
    if veredicto_ok and estado_ok:
        print("RESULTADO: coincide con lo esperado")
        return True
    print(f"RESULTADO: NO coincide. Esperado: {esperado}, rechazo esperado: {espera_rechazo}")
    return False


def main() -> None:
    modos = list(ACCIONES) + ["secuencia"]
    if len(sys.argv) != 3 or sys.argv[2] not in modos:
        sys.exit(f"Uso: probar_escrituras.py <id_wo> <{'|'.join(modos)}>")
    try:
        wo_id = int(sys.argv[1])   # id de la WO de prueba (valor genérico: el que muestre explorar_ordenes.py)
    except ValueError:
        sys.exit("<id_wo> tiene que ser un número entero")
    modo = sys.argv[2]

    wo = leer_orden(wo_id)
    if wo is None:
        sys.exit(f"No existe la orden de trabajo {wo_id}. Creá y confirmá una MO nueva en Odoo "
                 "y mirá el id real con: python3 scripts/explorar_ordenes.py | tail -n 3")

    if modo == "secuencia":
        pasos = SECUENCIA
        print(f"Se va a MODIFICAR la WO {wo_id}: {wo['name']} ({wo['production_id'][1]}), "
              f"estado actual: {wo['state']}.")
        print("Pasos:", ", ".join(a for a, _ in pasos))
        if input(f"Para continuar escribí el id ({wo_id}): ").strip() != str(wo_id):
            sys.exit("Cancelado, no se modificó nada.")
    else:
        pasos = [(modo, False)]

    for n, (accion, espera_rechazo) in enumerate(pasos, 1):
        print(f"\n===== PASO {n}/{len(pasos)}: {accion} =====")
        if not ejecutar_paso(wo_id, accion, espera_rechazo):
            print("Me detengo en el primer resultado inesperado. Pegame la salida completa.")
            sys.exit(1)

    print("\nTodos los pasos coinciden con lo esperado.")


if __name__ == "__main__":
    main()