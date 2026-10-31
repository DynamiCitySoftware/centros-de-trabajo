"""Prueba OdooBackend.enviar contra UNA WO real. MODIFICA DATOS REALES.

Uso (desde la raíz del repo, dentro de nix develop):
    python3 scripts/probar_backend.py <id_wo>
"""
import sys
from pathlib import Path

from centros_de_trabajo.backends.odoo import OdooBackend, OrdenNoExiste
from centros_de_trabajo.core.ordenes import Orden

URL = "https://torneria.dynamicity.com.ar"
DB = "torneria_db"
USER = "operador@gmail.com"
KEY_FILE = Path("/var/lib/centro-trabajo/odoo.key")

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
    if len(sys.argv) != 2:
        sys.exit("Uso: probar_backend.py <id_wo>")
    wo_id = int(sys.argv[1])   # id real de la WO de prueba, el que muestre explorar_ordenes.py
    backend = OdooBackend(URL, DB, USER, KEY_FILE)

    print("verificar:", backend.verificar())
    try:
        wo = backend.leer_orden(wo_id)
    except OrdenNoExiste as e:
        sys.exit(f"{e}. Creá y confirmá una MO nueva en Odoo y mirá el id real.")
    print(f"Se va a MODIFICAR la WO {wo_id}: {wo.nombre}, estado Odoo: {wo.state}")
    if input(f"Para continuar escribí el id ({wo_id}): ").strip() != str(wo_id):
        sys.exit("Cancelado, no se modificó nada.")

    for n, (orden, espera_ok) in enumerate(SECUENCIA, 1):
        resultado = backend.enviar(orden, wo_id)
        print(f"{n}/{len(SECUENCIA)} {orden.value:9} -> ok={resultado.ok} | {resultado.mensaje}")
        if resultado.ok != espera_ok:
            sys.exit(f"Inesperado: se esperaba ok={espera_ok}. Pegame esta salida.")
    print("Todos los pasos coinciden con lo esperado.")


if __name__ == "__main__":
    main()