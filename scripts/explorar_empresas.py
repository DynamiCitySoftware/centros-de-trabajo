import xmlrpc.client

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
LOGIN = "operador@gmail.com"
RUTA_CLAVE = "/var/lib/centro-trabajo/odoo.key"

clave = open(RUTA_CLAVE).read().strip()
uid = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common").authenticate(DB, LOGIN, clave, {})
modelos = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")


def ejecutar(modelo, metodo, args, kwargs=None):
    return modelos.execute_kw(DB, uid, clave, modelo, metodo, args, kwargs or {})


print("empresas existentes:")
for e in ejecutar("res.company", "search_read", [[]], {"fields": ["name"]}):
    print("  ", e)

print("\nusuarios 2 y 18:")
for u in ejecutar("res.users", "read", [[2, uid]], {"fields": ["login", "company_id", "company_ids"]}):
    print("  ", u)

print("\ncentros de trabajo (empresa y calendario):")
for c in ejecutar("mrp.workcenter", "search_read", [[]],
                  {"fields": ["name", "company_id", "resource_calendar_id"],
                   "context": {"active_test": False}}):
    print("  ", c)

print("\ncalendarios:")
for c in ejecutar("resource.calendar", "search_read", [[]],
                  {"fields": ["name", "company_id"], "context": {"active_test": False}}):
    print("  ", c)

print("\nórdenes de fabricación 2 y 3:")
for m in ejecutar("mrp.production", "read", [[2, 3]], {"fields": ["name", "company_id", "user_id"]}):
    print("  ", m)