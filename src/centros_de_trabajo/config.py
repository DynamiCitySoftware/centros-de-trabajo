import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Config:
    backend: str          # "fake" u "odoo"
    kiosco: bool          # True = pantalla completa
    odoo_url: str
    odoo_db: str
    odoo_user: str
    odoo_key_file: Path

    @classmethod
    def desde_entorno(cls) -> "Config":
        cfg = cls(
            backend=os.environ.get("BACKEND", "fake"),
            kiosco=os.environ.get("KIOSCO", "0") == "1",
            odoo_url=os.environ.get("ODOO_URL", ""),
            odoo_db=os.environ.get("ODOO_DB", ""),
            odoo_user=os.environ.get("ODOO_USER", ""),
            odoo_key_file=Path(os.environ.get("ODOO_KEY_FILE", "/var/lib/centro-trabajo/odoo.key")),
        )
        if cfg.backend == "odoo":
            requeridas = [("ODOO_URL", cfg.odoo_url), ("ODOO_DB", cfg.odoo_db), ("ODOO_USER", cfg.odoo_user)]
            faltan = [nombre for nombre, valor in requeridas if not valor]
            if faltan:
                raise ValueError(f"Con BACKEND=odoo faltan variables: {', '.join(faltan)}")
        return cfg