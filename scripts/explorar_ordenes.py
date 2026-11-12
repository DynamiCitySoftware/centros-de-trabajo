# Ruta: scripts/explorar_ordenes.py en PC LAB — reemplazar TODO el archivo
import sys
import xmlrpc.client

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
LOGIN = "operador@gmail.com"
RUTA_CLAVE = "/var/lib/centro-trabajo/odoo.key"

clave_api = open(RUTA_CLAVE).read().strip()
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid_autenticado = common.authenticate(DB, LOGIN, clave_api, {})
proxy_objeto = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def ejecutar(nombre_modelo_odoo, nombre_metodo, argumentos_posicionales, opciones_kwargs=None):
    """Ejecuta un método Odoo. nombre_modelo_odoo es string, ej: 'mrp.workorder'."""
    return proxy_objeto.execute_kw(DB, uid_autenticado, clave_api, nombre_modelo_odoo, nombre_metodo, argumentos_posicionales, opciones_kwargs or {})


def obtener_cantidad_limite_desde_argumentos() -> int | None:
    """Devuelve N si se pasó como `python3 scripts/explorar_ordenes.py N`, None = traer todo."""
    if len(sys.argv) == 1:
        return None
    if len(sys.argv) > 2:
        print(f"Uso: {sys.argv[0]} [N_ultimas_ordenes]")
        sys.exit(2)
    try:
        cantidad_solicitada = int(sys.argv[1])
    except ValueError:
        print(f"Uso: {sys.argv[0]} [N_ultimas_ordenes] — N debe ser entero positivo")
        sys.exit(2)
    if cantidad_solicitada <= 0:
        print("N debe ser mayor que 0")
        sys.exit(2)
    return cantidad_solicitada


print("uid:", uid_autenticado)
for permiso in ("read", "write"):
    try:
        tiene_permiso = ejecutar("mrp.workorder", "check_access_rights", [permiso], {"raise_exception": False})
    except Exception as e:
        tiene_permiso = f"no se pudo comprobar ({e})"
    print(f"permiso {permiso} en mrp.workorder:", tiene_permiso)

cantidad_limite = obtener_cantidad_limite_desde_argumentos()

campos_a_traer = ["name", "state", "is_user_working", "working_state", "production_id",
          "production_state", "workcenter_id", "qty_remaining", "qty_producing",
          "duration", "duration_expected", "working_user_ids"]

opciones_consulta = {"fields": campos_a_traer, "order": "id desc"}
if cantidad_limite is not None:
    opciones_consulta["limit"] = cantidad_limite

# Dominio vacío = Todo, para que el default muestre todo como pediste.
# Antes yo te había puesto un filtro de production_state, eso te recortaba.
ordenes_recientes = ejecutar("mrp.workorder", "search_read", [[]], opciones_consulta)
# Las traemos con `id desc` para quedarnos con las últimas N,
# y las mostramos en ascendente para leer como la UI (22,23...36).
ordenes_recientes = sorted(ordenes_recientes, key=lambda o: o["id"])

if cantidad_limite is None:
    print(f"órdenes de trabajo (todas): {len(ordenes_recientes)}")
else:
    print(f"órdenes de trabajo (últimas {cantidad_limite}): {len(ordenes_recientes)}")
for orden in ordenes_recientes:
    print(orden)

ids_ordenes = [o["id"] for o in ordenes_recientes]
if ids_ordenes:
    cronometros_abiertos = ejecutar(
        "mrp.workcenter.productivity", "search_read",
        [[("workorder_id", "in", ids_ordenes), ("date_end", "=", False)]],
        {"fields": ["workorder_id", "user_id", "date_start"]},
    )
    print("cronómetros abiertos:", cronometros_abiertos)