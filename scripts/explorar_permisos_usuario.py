#!/usr/bin/env python3
"""Lista los permisos efectivos de un usuario de Odoo 18 (solo lectura).

Uso:
    python3 odoo_permisos.py operador@gmail.com
    python3 odoo_permisos.py operador@gmail.com --menus --solo-modelo mrp
"""
import argparse
import getpass
import os
import sys
import xmlrpc.client

import io
from pathlib import Path

class Tee:
    """Escribe en varios destinos a la vez (pantalla + buffer)."""
    def __init__(self, *destinos):
        self.destinos = destinos

    def write(self, texto):
        for d in self.destinos:
            d.write(texto)

    def flush(self):
        for d in self.destinos:
            d.flush()

# Valores por defecto. ODOO_DB es un PLACEHOLDER GENERICO: reemplazalo por
# el nombre real de tu base (o exportá la variable de entorno ODOO_DB).
URL = os.environ.get("ODOO_URL", "https://torneria.dynamicity.com.ar")
DB = os.environ.get("ODOO_DB", "torneria_db")
ADMIN_LOGIN = os.environ.get("ODOO_ADMIN_LOGIN", "admin")  # placeholder generico


def main():
    ap = argparse.ArgumentParser(description="Permisos de un usuario de Odoo")

    buffer = io.StringIO()
    stdout_original = sys.stdout
    sys.stdout = Tee(stdout_original, buffer)

    ap.add_argument("login", help="login del usuario a revisar (mail de creación)")
    ap.add_argument("--menus", action="store_true", help="listar menús restringidos")
    ap.add_argument("--solo-modelo", default="", help="filtrar modelos por texto (ej: mrp)")
    args = ap.parse_args()

    if "<" in DB or "<" in ADMIN_LOGIN:
        sys.exit("Falta configurar ODOO_DB y ODOO_ADMIN_LOGIN (variables de entorno).")

    # Credenciales del usuario que CONSULTA (necesita ser admin/ajustes técnicos).
    password = os.environ.get("ODOO_PASSWORD") or getpass.getpass(
        f"Contraseña o API key de {ADMIN_LOGIN}: ")

    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common")
    uid = common.authenticate(DB, ADMIN_LOGIN, password, {})
    if not uid:
        sys.exit("Autenticación fallida (revisá DB, login y contraseña).")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object")

    def call(model, method, domain_or_ids, **kw):
        return models.execute_kw(DB, uid, password, model, method, [domain_or_ids], kw)

    # 1. Usuario (active_test False para encontrar también usuarios archivados)
    users = call("res.users", "search_read", [("login", "=", args.login)],
                 fields=["name", "login", "active", "share", "groups_id",
                         "company_id", "company_ids"],
                 context={"active_test": False})
    if not users:
        sys.exit(f"No existe un usuario con login '{args.login}'.")
    u = users[0]
    gids = u["groups_id"]

    print("=" * 70)
    print(f"Usuario : {u['name']} <{u['login']}>  (id {u['id']})")
    print(f"Activo  : {u['active']}   Portal/compartido: {u['share']}")
    print(f"Empresa : {u['company_id'][1] if u['company_id'] else '-'}"
          f"   (empresas permitidas: {u['company_ids']})")

    # 2. Grupos
    groups = call("res.groups", "read", gids, fields=["full_name"])
    print(f"\n--- GRUPOS ({len(groups)}) ---")
    for g in sorted(groups, key=lambda x: x["full_name"]):
        print(f"  [{g['id']}] {g['full_name']}")

    # 3. Permisos por modelo (ACL): se suman con OR entre grupos
    acls = call("ir.model.access", "search_read",
                ["|", ("group_id", "in", gids), ("group_id", "=", False)],
                fields=["model_id", "perm_read", "perm_write",
                        "perm_create", "perm_unlink"])
    model_ids = list({a["model_id"][0] for a in acls})
    model_names = {m["id"]: m["model"] for m in
                   call("ir.model", "read", model_ids, fields=["model"])}
    efectivo = {}
    for a in acls:
        nombre = model_names[a["model_id"][0]]
        cur = efectivo.setdefault(nombre, [False] * 4)
        for i, k in enumerate(("perm_read", "perm_write", "perm_create", "perm_unlink")):
            cur[i] = cur[i] or a[k]

    print(f"\n--- ACCESO POR MODELO (R=leer W=editar C=crear D=borrar) ---")
    for nombre in sorted(efectivo):
        if args.solo_modelo and args.solo_modelo not in nombre:
            continue
        r, w, c, d = efectivo[nombre]
        print(f"  {nombre:<45} "
              f"{'R' if r else '-'}{'W' if w else '-'}{'C' if c else '-'}{'D' if d else '-'}")

    # 4. Reglas de registro (filtros de filas)
    rules = call("ir.rule", "search_read",
                 ["|", ("groups", "in", gids), ("groups", "=", False)],
                 fields=["name", "model_id", "domain_force", "groups",
                         "perm_read", "perm_write", "perm_create", "perm_unlink"])
    print(f"\n--- REGLAS DE REGISTRO ({len(rules)}) ---")
    for r in sorted(rules, key=lambda x: x["model_id"][1]):
        if args.solo_modelo and args.solo_modelo not in r["model_id"][1].lower():
            continue
        alcance = "GLOBAL" if not r["groups"] else "por grupo"
        perms = "".join(l if r[k] else "-" for l, k in
                        zip("RWCD", ("perm_read", "perm_write", "perm_create", "perm_unlink")))
        print(f"  [{alcance}] {r['model_id'][1]} | {r['name']} | {perms}")
        print(f"      dominio: {r['domain_force']}")

    # 5. Menús restringidos a grupos del usuario (opcional)
    if args.menus:
        menus = call("ir.ui.menu", "search_read", [("groups_id", "in", gids)],
                     fields=["complete_name"])
        print(f"\n--- MENÚS RESTRINGIDOS VISIBLES ({len(menus)}) ---")
        for m in sorted(menus, key=lambda x: x["complete_name"]):
            print(f"  {m['complete_name']}")
    
    sys.stdout = stdout_original
    salida = Path("salidas") / f"{args.login.replace('/', '_')}.txt"
    salida.parent.mkdir(exist_ok=True)
    salida.write_text(buffer.getvalue(), encoding="utf-8")
    print(f"\nSalida guardada en: {salida.resolve()}")


if __name__ == "__main__":
    main()