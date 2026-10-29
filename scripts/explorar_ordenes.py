import xmlrpc.client

URL = "https://torneria.dynamicity.com.ar"   # confirmado en la Fase 1
DB = "torneria_db"                      # valor genérico: poné el nombre real de la base
LOGIN = "operador@gmail.com"                  # confirmado en la Fase 1
RUTA_CLAVE = "/var/lib/centro-trabajo/odoo.key"

clave = open(RUTA_CLAVE).read().strip()
common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
uid = common.authenticate(DB, LOGIN, clave, {})
modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def ejecutar(modelo, metodo, args, kwargs=None):
    return modelos.execute_kw(DB, uid, clave, modelo, metodo, args, kwargs or {})


print("uid:", uid)
for permiso in ("read", "write"):
    try:
        ok = ejecutar("mrp.workorder", "check_access_rights", [permiso], {"raise_exception": False})
    except Exception as e:
        ok = f"no se pudo comprobar ({e})"
    print(f"permiso {permiso} en mrp.workorder:", ok)

campos = ["name", "state", "is_user_working", "working_state", "production_id",
          "production_state", "workcenter_id", "qty_remaining", "qty_producing",
          "duration", "duration_expected", "working_user_ids"]
ordenes = ejecutar(
    "mrp.workorder", "search_read",
    [[("production_state", "not in", ["draft", "done", "cancel"])]],
    {"fields": campos, "limit": 20},
)
print("órdenes de trabajo:", len(ordenes))
for o in ordenes:
    print(o)

ids = [o["id"] for o in ordenes]
if ids:
    abiertos = ejecutar(
        "mrp.workcenter.productivity", "search_read",
        [[("workorder_id", "in", ids), ("date_end", "=", False)]],
        {"fields": ["workorder_id", "user_id", "loss_id", "date_start"]},
    )
    print("cronómetros abiertos:", abiertos)