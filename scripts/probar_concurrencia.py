"""Lectura o una acción aislada sobre una WO real de Odoo.

Las acciones iniciar, pausar, reanudar y terminar modifican datos reales.
Uso desde la raíz del repo, dentro de nix develop:
    python3 scripts/probar_concurrencia.py <usuario> <ruta_clave> <id_wo> <leer|iniciar|pausar|reanudar|terminar>
"""
import argparse
import sys
import xmlrpc.client
from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend, OrdenNoExiste
from centros_de_trabajo.core.estado import derivar_estado
from centros_de_trabajo.core.ordenes import Orden

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"

ACCIONES = {
    "iniciar": Orden.INICIAR,
    "pausar": Orden.PAUSAR,
    "reanudar": Orden.REANUDAR,
    "terminar": Orden.TERMINAR,
}


def mostrar(backend: OdooBackend, id_wo: int) -> None:
    wo = backend.leer_orden(id_wo)
    print(
        f"WO {wo.id}: {wo.nombre} | "
        f"state Odoo={wo.state} | "
        f"is_user_working={wo.is_user_working} | "
        f"otros_trabajando={wo.otros_trabajando} | "
        f"working_state={wo.working_state} | "
        f"estado kiosco={derivar_estado(wo).value}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Prueba controlada de concurrencia en una WO")
    parser.add_argument("usuario", help="login real del usuario de Odoo")
    parser.add_argument("ruta_clave", type=Path, help="ruta al archivo que contiene solo su API key")
    parser.add_argument("id_wo", type=int, help="ID real de mrp.workorder")
    parser.add_argument("accion", choices=["leer", *ACCIONES])
    args = parser.parse_args()

    backend = OdooBackend(URL, DB, args.usuario, args.ruta_clave)

    verificacion = backend.verificar()
    print("verificar:", verificacion)
    if not verificacion.ok:
        sys.exit("Falló la conexión o autenticación; no se intentó ninguna acción.")

    try:
        print("ANTES:")
        mostrar(backend, args.id_wo)
    except OrdenNoExiste as error:
        sys.exit(f"{error}. Revisá el ID real de la WO.")
    except xmlrpc.client.Fault as error:
        sys.exit(f"Odoo rechazó la lectura: {error.faultString[-500:]}")

    if args.accion == "leer":
        return

    confirmacion = f"{args.id_wo}:{args.accion}"
    if input(f"Para enviar esta acción escribí exactamente {confirmacion}: ").strip() != confirmacion:
        sys.exit("Cancelado; no se envió la acción.")

    resultado = backend.enviar(ACCIONES[args.accion], args.id_wo)
    print(f"RESULTADO: ok={resultado.ok} | {resultado.mensaje}")

    try:
        print("DESPUÉS:")
        mostrar(backend, args.id_wo)
    except (OrdenNoExiste, xmlrpc.client.Fault) as error:
        sys.exit(f"No pude releer la WO después de la acción: {error}")


if __name__ == "__main__":
    main()