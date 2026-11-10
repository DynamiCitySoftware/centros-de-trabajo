"""Prueba listar_ordenes() contra Odoo real. Solo lectura.

Uso:
    python3 scripts/probar_listar_backend.py <usuario> <ruta_clave>
"""
import argparse
import sys
import xmlrpc.client
from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend


URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
TAMANO_PAGINA_PRUEBA = 200

# WO confirmadas en las pruebas anteriores:
# 21, 22 y 23 estaban ready.
# 20 quedó done tras cerrar WH/MO/00021.
WO_REFERENCIA = {
    20: "done",
    21: "ready",
    22: "ready",
    23: "ready",
}


def imprimir_ordenes(ordenes) -> dict[int, object]:
    print(f"\n--- listar_ordenes(): {len(ordenes)} órdenes ---")
    por_id = {}

    for orden in sorted(ordenes, key=lambda elemento: elemento.id):
        print(
            f"id={orden.id} | nombre={orden.nombre} | "
            f"state Odoo={orden.state} | "
            f"is_user_working={orden.is_user_working} | "
            f"otros_trabajando={orden.otros_trabajando}"
        )
        por_id[orden.id] = orden

    if len(por_id) != len(ordenes):
        print("[ERROR] Hay IDs duplicados en el resultado.")

    return por_id


def consultar_ready_done(backend: OdooBackend, state: str) -> set[int]:
    """Consulta directa, solo lectura, para verificar que el listado no omita
    WO ready/done que el usuario puede leer.
    """
    ids = set()
    offset = 0

    while True:
        pagina = backend._ejecutar(
            "mrp.workorder",
            "search_read",
            [[("state", "=", state)]],
            {
                "fields": ["id"],
                "limit": TAMANO_PAGINA_PRUEBA,
                "offset": offset,
                "order": "id asc",
            },
        )

        if not pagina:
            break

        ids.update(fila["id"] for fila in pagina)

        if len(pagina) < TAMANO_PAGINA_PRUEBA:
            break

        offset += len(pagina)

    return ids


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prueba de solo lectura del listado real de WO."
    )
    parser.add_argument("usuario", help="login real de Odoo")
    parser.add_argument(
        "ruta_clave",
        type=Path,
        help="ruta del archivo que contiene la clave de ese usuario",
    )
    args = parser.parse_args()

    backend = OdooBackend(URL, DB, args.usuario, args.ruta_clave)

    verificacion = backend.verificar()
    print("verificar:", verificacion)
    if not verificacion.ok:
        sys.exit("Falló la conexión o autenticación; no se consultó el listado.")

    try:
        ordenes = backend.listar_ordenes()
        por_id = imprimir_ordenes(ordenes)

        print("\n--- Comprobación de completitud para ready/done ---")
        faltantes = set()

        for state in ("ready", "done"):
            ids_estado = consultar_ready_done(backend, state)
            faltan_estado = ids_estado - por_id.keys()
            faltantes.update(faltan_estado)
            print(
                f"state={state}: Odoo permite leer {len(ids_estado)}; "
                f"faltan en listar_ordenes(): {sorted(faltan_estado)}"
            )

        print("\n--- WO de referencia ---")
        fallas = 0

        for wo_id, state_esperado in WO_REFERENCIA.items():
            orden = por_id.get(wo_id)
            ok = orden is not None and orden.state == state_esperado
            print(
                f"[{'OK' if ok else 'REVISAR'}] WO {wo_id}: "
                f"esperado state={state_esperado}; "
                f"recibido={orden.state if orden else 'no aparece'}"
            )
            fallas += not ok

        if faltantes:
            print(f"[REVISAR] El listado omitió WO ready/done: {sorted(faltantes)}")
            fallas += 1

        if fallas:
            print(f"\nHay {fallas} comprobación(es) para investigar.")
        else:
            print("\nLas comprobaciones coinciden. No se modificó Odoo.")

    except xmlrpc.client.Fault as error:
        sys.exit(f"Odoo rechazó la consulta: {error.faultString[-500:]}")
    except (AttributeError, KeyError) as error:
        sys.exit(f"Falta un método/campo esperado en el backend: {error}")


if __name__ == "__main__":
    main()