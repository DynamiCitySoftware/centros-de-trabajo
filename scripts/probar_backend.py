"""Prueba OdooBackend.enviar contra UNA WO real. MODIFICA DATOS REALES.

Uso (desde la raíz del repo, dentro de nix develop):
    python3 scripts/probar_backend.py <usuario> <ruta_clave> <id_wo>
"""
import argparse
import sys
import xmlrpc.client
from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend, OrdenNoExiste
from centros_de_trabajo.core.ordenes import Orden

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"

# (orden, ¿esperamos ok=True?). Las repetidas ahora las rechaza el kiosco
# ANTES de llegar a Odoo (a diferencia de probar_escrituras.py).
SECUENCIA = [
    (Orden.INICIAR, True),
    (Orden.INICIAR, False),
    (Orden.PAUSAR, True),
    (Orden.PAUSAR, False),
    (Orden.REANUDAR, True),
    (Orden.PAUSAR, True),
    (Orden.TERMINAR, True),
    (Orden.INICIAR, False),
]


def main() -> None:
    ap = argparse.ArgumentParser(description="Prueba OdooBackend contra una WO real")
    ap.add_argument("usuario", help="login del usuario de Odoo (valor genérico: el del operario de prueba)")
    ap.add_argument("ruta_clave", type=Path, help="archivo con la API key de ese usuario")
    ap.add_argument("id_wo", type=int, help="id real de la WO de prueba (lo muestra explorar_ordenes.py)")
    args = ap.parse_args()

    backend = OdooBackend(URL, DB, args.usuario, args.ruta_clave)

    verificacion = backend.verificar()
    print("verificar:", verificacion)
    if not verificacion.ok:
        sys.exit("No se pudo conectar con ese usuario y esa clave. No se modificó nada.")

    try:
        wo = backend.leer_orden(args.id_wo)
    except OrdenNoExiste as e:
        sys.exit(f"{e}. Creá y confirmá una MO nueva en Odoo y mirá el id real.")
    except xmlrpc.client.Fault as e:
        sys.exit(f"Odoo rechazó la lectura (¿permisos?): {e.faultString[-300:]}")

    print(f"Usuario: {args.usuario}")
    print(f"Se va a MODIFICAR la WO {args.id_wo}: {wo.nombre}, estado Odoo: {wo.state}")
    if input(f"Para continuar escribí el id ({args.id_wo}): ").strip() != str(args.id_wo):
        sys.exit("Cancelado, no se modificó nada.")

    for n, (orden, espera_ok) in enumerate(SECUENCIA, 1):
        resultado = backend.enviar(orden, args.id_wo)
        print(f"{n}/{len(SECUENCIA)} {orden.value:9} -> ok={resultado.ok} | {resultado.mensaje}")
        if resultado.ok != espera_ok:
            sys.exit(f"Inesperado: se esperaba ok={espera_ok}. Pegame esta salida.")
    print("Todos los pasos coinciden con lo esperado.")


if __name__ == "__main__":
    main()