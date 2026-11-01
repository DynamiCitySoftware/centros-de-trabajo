# centros_de_trabajo

Kiosco en PyQt6 para que los operarios inicien, pausen, reanuden y terminen
órdenes de trabajo (`mrp.workorder`) de Odoo 18 Community. **Odoo es la única
fuente de verdad**: el kiosco no guarda el estado de las órdenes.

## Estado actual

| Componente | Estado |
|---|---|
| Conexión XML-RPC a Odoo | Hecho y probado |
| Estado derivado de Odoo (`core/estado.py`) | Hecho y probado |
| `OdooBackend.enviar(orden, id_orden)` | Hecho y probado contra Odoo real |
| `FakeBackend` | Hecho (todavía no simula estados) |
| Listado de órdenes del operario | Pendiente |
| Login por pantalla | Pendiente |
| UI conectada al backend (`__main__.py`) | Pendiente (hoy está vacío) |
| Módulo NixOS (`nix/module.nix`) | Pendiente (hoy está vacío) |

La UI actual (`ui/interfaz_principal.py`) es un prototipo con 4 botones
(F1 a F4) que todavía no llama al backend.

## Cómo funciona

1. El kiosco lee la orden de trabajo desde Odoo (`state`, `is_user_working`,
   `working_user_ids`, `working_state`).
2. `derivar_estado` la traduce a un estado del kiosco.
3. Si la orden pedida es válida para ese estado, se llama al botón de Odoo.
4. Se vuelve a leer la orden y se comprueba el resultado (postcondición).

### Estados derivados

| Estado kiosco | Condición en Odoo |
|---|---|
| `DETENIDO` | `state=ready` |
| `EN_CURSO` | `state=progress` y yo tengo el cronómetro abierto |
| `PAUSADO` | `state=progress` y nadie trabaja |
| `OCUPADO` | `state=progress` y trabaja otro usuario |
| `BLOQUEADO` | el centro de trabajo está bloqueado (`working_state=blocked`) |
| `NO_DISPONIBLE` | `state=pending` o `waiting` |
| `TERMINADO` | `state=done` |
| `CANCELADO` | `state=cancel` |

### Órdenes y botones de Odoo

| Orden | Botón de Odoo | Nota |
|---|---|---|
| `INICIAR` | `button_start` | Devuelve `None` (ver más abajo) |
| `REANUDAR` | `button_start` | Crea un cronómetro nuevo |
| `PAUSAR` | `button_pending` | Cierra el cronómetro; la WO sigue en `progress` |
| `TERMINAR` | `button_finish` | Devuelve `True`; funciona también desde pausa |

Dos particularidades medidas contra el Odoo real:

- `button_start` y `button_pending` devuelven `None`. El servidor falla al
  serializarlo con `cannot marshal None`, **pero la acción sí se ejecuta**. El
  backend tolera solo ese `Fault` y confirma releyendo la orden.
- Terminar la WO **no cierra la MO**: queda en `to_close`. El consumo de stock
  se registra cuando el administrador pulsa **Producir todo** en la MO.

## Estructura

```
src/centros_de_trabajo/
  config.py            configuración por variables de entorno
  core/ordenes.py      Orden (4 comandos) y OrdenDeTrabajo (dato leído de Odoo)
  core/estado.py       estados derivados, transiciones y postcondiciones
  backends/base.py     contrato Backend y Resultado
  backends/fake.py     backend de prueba sin red
  backends/odoo.py     backend real (XML-RPC)
  ui/                  interfaz PyQt6
scripts/               exploración y pruebas contra Odoo (ver manual)
tests/                 pytest sin red
```

## Desarrollo

Entorno (NixOS):

```bash
nix develop
pytest
```

Última ejecución informada: `59 passed`.

## Configuración

| Variable | Descripción |
|---|---|
| `BACKEND` | `fake` (por defecto) u `odoo` |
| `KIOSCO` | `1` para pantalla completa |
| `ODOO_URL` | URL base, sin ruta y sin `/` final |
| `ODOO_DB` | nombre de la base |
| `ODOO_USER` | login del usuario de Odoo |
| `ODOO_KEY_FILE` | archivo con la API key (por defecto `/var/lib/centro-trabajo/odoo.key`) |

Un archivo de clave por usuario, con permisos `600`. Los `*.key` están en
`.gitignore`; no se versionan.

## Modelo de usuarios

Un usuario de Odoo por operario, con permisos **Manufacturing / User**. Se
verificó que alcanza para iniciar, pausar, reanudar y terminar órdenes.
Stock y listas de materiales los modifica solo el administrador.

## Limitaciones conocidas

- No se probó concurrencia real (dos solicitudes exactamente simultáneas).
- No se probaron cortes de red durante una escritura.
- Terminar una WO mientras otro usuario tiene el cronómetro abierto: el kiosco
  lo rechaza (`OCUPADO`); el comportamiento de Odoo (`end_all` cierra todos
  los cronómetros) no se ejercitó a propósito.
- El texto `cannot marshal None` depende de la versión de Python del servidor.
  La garantía real es la relectura posterior.