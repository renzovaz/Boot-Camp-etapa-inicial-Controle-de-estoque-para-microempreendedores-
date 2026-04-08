"""Módulo de persistência do StockGuard.

Salva e carrega o inventário em arquivo JSON local.
"""

from __future__ import annotations

import json
from pathlib import Path

from stockguard.inventory import Inventory

DEFAULT_DATA_FILE = Path.home() / ".stockguard" / "inventory.json"


class Storage:
    """Gerencia a persistência do inventário em arquivo JSON."""

    def __init__(self, filepath: Path = DEFAULT_DATA_FILE) -> None:
        self.filepath = Path(filepath)

    def save(self, inventory: Inventory) -> None:
        """Persiste o inventário em disco."""
        self.filepath.parent.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(inventory.to_dict(), f, ensure_ascii=False, indent=2)

    def load(self) -> Inventory:
        """Carrega o inventário do disco. Retorna vazio se não existir."""
        if not self.filepath.exists():
            return Inventory()
        with open(self.filepath, encoding="utf-8") as f:
            data = json.load(f)
        return Inventory.from_dict(data)
