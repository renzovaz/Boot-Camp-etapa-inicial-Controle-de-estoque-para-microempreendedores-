"""Módulo de lógica de negócio do StockGuard.

Gerencia operações de estoque: cadastro, baixa, consulta e alertas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Product:
    """Representa um produto no estoque."""

    name: str
    quantity: int
    min_stock: int
    unit_price: float
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    total_sold: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "quantity": self.quantity,
            "min_stock": self.min_stock,
            "unit_price": self.unit_price,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "total_sold": self.total_sold,
        }

    @classmethod
    def from_dict(cls, data: dict) -> Product:
        return cls(
            name=data["name"],
            quantity=data["quantity"],
            min_stock=data["min_stock"],
            unit_price=data["unit_price"],
            created_at=data.get("created_at", datetime.now().isoformat()),
            updated_at=data.get("updated_at", datetime.now().isoformat()),
            total_sold=data.get("total_sold", 0),
        )


class InventoryError(Exception):
    """Erro base para operações de estoque."""


class ProductNotFoundError(InventoryError):
    """Produto não encontrado no estoque."""


class InsufficientStockError(InventoryError):
    """Quantidade insuficiente no estoque."""


class InvalidQuantityError(InventoryError):
    """Quantidade inválida (zero ou negativa)."""


class Inventory:
    """Gerencia o inventário de produtos."""

    def __init__(self, products: dict[str, Product] | None = None) -> None:
        self._products: dict[str, Product] = products or {}

    def _normalize_name(self, name: str) -> str:
        return name.strip().lower()

    def add_product(
        self,
        name: str,
        quantity: int,
        min_stock: int,
        unit_price: float,
    ) -> Product:
        """Cadastra ou atualiza um produto no estoque."""
        if quantity < 0:
            raise InvalidQuantityError("Quantidade não pode ser negativa.")
        if min_stock < 0:
            raise InvalidQuantityError("Estoque mínimo não pode ser negativo.")
        if unit_price < 0:
            raise InvalidQuantityError("Preço unitário não pode ser negativo.")
        if not name or not name.strip():
            raise ValueError("Nome do produto não pode ser vazio.")

        key = self._normalize_name(name)
        if key in self._products:
            product = self._products[key]
            product.quantity += quantity
            product.min_stock = min_stock
            product.unit_price = unit_price
            product.updated_at = datetime.now().isoformat()
        else:
            product = Product(
                name=name.strip(),
                quantity=quantity,
                min_stock=min_stock,
                unit_price=unit_price,
            )
            self._products[key] = product

        return product

    def sell_product(self, name: str, quantity: int) -> Product:
        """Registra a venda (baixa) de um produto."""
        if quantity <= 0:
            raise InvalidQuantityError("Quantidade vendida deve ser maior que zero.")

        key = self._normalize_name(name)
        if key not in self._products:
            raise ProductNotFoundError(f"Produto '{name}' não encontrado.")

        product = self._products[key]
        if product.quantity < quantity:
            raise InsufficientStockError(
                f"Estoque insuficiente. Disponível: {product.quantity}, "
                f"solicitado: {quantity}."
            )

        product.quantity -= quantity
        product.total_sold += quantity
        product.updated_at = datetime.now().isoformat()
        return product

    def get_product(self, name: str) -> Product:
        """Retorna um produto pelo nome."""
        key = self._normalize_name(name)
        if key not in self._products:
            raise ProductNotFoundError(f"Produto '{name}' não encontrado.")
        return self._products[key]

    def list_products(self) -> list[Product]:
        """Lista todos os produtos ordenados por nome."""
        return sorted(self._products.values(), key=lambda p: p.name.lower())

    def low_stock_alerts(self) -> list[Product]:
        """Retorna produtos com estoque abaixo do mínimo."""
        return [p for p in self._products.values() if p.quantity <= p.min_stock]

    def turnover_report(self) -> list[dict]:
        """Gera relatório de giro de mercadorias."""
        report = []
        for product in self.list_products():
            total_value_sold = product.total_sold * product.unit_price
            current_value = product.quantity * product.unit_price
            report.append(
                {
                    "name": product.name,
                    "quantity": product.quantity,
                    "total_sold": product.total_sold,
                    "unit_price": product.unit_price,
                    "total_value_sold": total_value_sold,
                    "current_stock_value": current_value,
                    "below_min": product.quantity <= product.min_stock,
                }
            )
        return sorted(report, key=lambda r: r["total_sold"], reverse=True)

    def remove_product(self, name: str) -> Product:
        """Remove um produto do inventário."""
        key = self._normalize_name(name)
        if key not in self._products:
            raise ProductNotFoundError(f"Produto '{name}' não encontrado.")
        return self._products.pop(key)

    def to_dict(self) -> dict:
        return {k: v.to_dict() for k, v in self._products.items()}

    @classmethod
    def from_dict(cls, data: dict) -> Inventory:
        products = {k: Product.from_dict(v) for k, v in data.items()}
        return cls(products=products)