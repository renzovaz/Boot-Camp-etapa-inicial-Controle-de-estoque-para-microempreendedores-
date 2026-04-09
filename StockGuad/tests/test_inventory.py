"""Testes automatizados do StockGuard.

Cobre caminho feliz, entradas inválidas e casos limite.
"""

import StockGuad.tests.test_inventory as test_inventory 

from stockguard.inventory import (
    InsufficientStockError,
    InvalidQuantityError,
    Inventory,
    ProductNotFoundError,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────


@test_inventory.fixture()
def inv() -> Inventory:
    """Inventário vazio para cada teste."""
    return Inventory()


@test_inventory.fixture()
def inv_with_products() -> Inventory:
    """Inventário com produtos pré-cadastrados."""
    inventory = Inventory()
    inventory.add_product("Caneta Azul", quantity=50, min_stock=10, unit_price=1.50)
    inventory.add_product("Caderno A4", quantity=20, min_stock=5, unit_price=12.00)
    inventory.add_product("Borracha", quantity=8, min_stock=15, unit_price=0.80)
    return inventory


# ─── Testes: add_product ──────────────────────────────────────────────────────


class TestAddProduct:
    def test_add_new_product_success(self, inv: Inventory) -> None:
        """Caminho feliz: cadastrar produto novo."""
        product = inv.add_product("Caneta", quantity=100, min_stock=10, unit_price=2.50)
        assert product.name == "Caneta"
        assert product.quantity == 100
        assert product.min_stock == 10
        assert product.unit_price == 2.50

    def test_add_product_replenishment_accumulates(self, inv: Inventory) -> None:
        """Reposição acumula quantidade."""
        inv.add_product("Caneta", quantity=50, min_stock=10, unit_price=2.50)
        inv.add_product("Caneta", quantity=30, min_stock=10, unit_price=2.50)
        product = inv.get_product("Caneta")
        assert product.quantity == 80

    def test_add_product_case_insensitive(self, inv: Inventory) -> None:
        """Nome do produto é case-insensitive."""
        inv.add_product("caneta", quantity=10, min_stock=5, unit_price=2.00)
        product = inv.get_product("CANETA")
        assert product.quantity == 10

    def test_add_product_negative_quantity_raises(self, inv: Inventory) -> None:
        """Quantidade negativa deve lançar InvalidQuantityError."""
        with test_inventory.raises(InvalidQuantityError, match="negativa"):
            inv.add_product("Caneta", quantity=-5, min_stock=10, unit_price=2.50)

    def test_add_product_negative_price_raises(self, inv: Inventory) -> None:
        """Preço negativo deve lançar InvalidQuantityError."""
        with test_inventory.raises(InvalidQuantityError, match="negativo"):
            inv.add_product("Caneta", quantity=10, min_stock=5, unit_price=-1.00)

    def test_add_product_empty_name_raises(self, inv: Inventory) -> None:
        """Nome vazio deve lançar ValueError."""
        with test_inventory.raises(ValueError):
            inv.add_product("   ", quantity=10, min_stock=5, unit_price=1.00)

    def test_add_product_zero_quantity_allowed(self, inv: Inventory) -> None:
        """Quantidade zero deve ser permitida (reserva de posição)."""
        product = inv.add_product("Caneta", quantity=0, min_stock=5, unit_price=2.00)
        assert product.quantity == 0


# ─── Testes: sell_product ────────────────────────────────────────────────────


class TestSellProduct:
    def test_sell_success(self, inv_with_products: Inventory) -> None:
        """Caminho feliz: vender produto disponível."""
        product = inv_with_products.sell_product("Caneta Azul", quantity=10)
        assert product.quantity == 40
        assert product.total_sold == 10

    def test_sell_accumulates_total_sold(self, inv_with_products: Inventory) -> None:
        """Vendas acumulam total_sold corretamente."""
        inv_with_products.sell_product("Caneta Azul", quantity=5)
        inv_with_products.sell_product("Caneta Azul", quantity=3)
        product = inv_with_products.get_product("Caneta Azul")
        assert product.total_sold == 8

    def test_sell_product_not_found_raises(self, inv: Inventory) -> None:
        """Produto inexistente deve lançar ProductNotFoundError."""
        with test_inventory.raises(ProductNotFoundError, match="não encontrado"):
            inv.sell_product("Produto Fantasma", quantity=1)

    def test_sell_insufficient_stock_raises(self, inv_with_products: Inventory) -> None:
        """Venda maior que estoque deve lançar InsufficientStockError."""
        with test_inventory.raises(InsufficientStockError, match="insuficiente"):
            inv_with_products.sell_product("Caneta Azul", quantity=9999)

    def test_sell_zero_quantity_raises(self, inv_with_products: Inventory) -> None:
        """Venda de zero unidades deve lançar InvalidQuantityError."""
        with test_inventory.raises(InvalidQuantityError, match="maior que zero"):
            inv_with_products.sell_product("Caneta Azul", quantity=0)

    def test_sell_negative_quantity_raises(self, inv_with_products: Inventory) -> None:
        """Venda negativa deve lançar InvalidQuantityError."""
        with test_inventory.raises(InvalidQuantityError):
            inv_with_products.sell_product("Caneta Azul", quantity=-3)

    def test_sell_exact_stock_reduces_to_zero(self, inv: Inventory) -> None:
        """Caso limite: vender exatamente o que há em estoque."""
        inv.add_product("Produto", quantity=5, min_stock=0, unit_price=10.00)
        product = inv.sell_product("Produto", quantity=5)
        assert product.quantity == 0


# ─── Testes: alertas e relatório ─────────────────────────────────────────────


class TestAlertsAndReport:
    def test_low_stock_alerts_returns_below_min(self, inv_with_products: Inventory) -> None:
        """low_stock_alerts deve retornar somente produtos abaixo do mínimo."""
        alerts = inv_with_products.low_stock_alerts()
        names = [p.name for p in alerts]
        assert "Borracha" in names
        assert "Caneta Azul" not in names

    def test_no_alerts_when_stock_ok(self, inv: Inventory) -> None:
        """Sem alertas quando todos os produtos estão acima do mínimo."""
        inv.add_product("Produto", quantity=100, min_stock=5, unit_price=1.00)
        assert inv.low_stock_alerts() == []

    def test_turnover_report_sorted_by_sold(self, inv_with_products: Inventory) -> None:
        """Relatório de giro ordenado por total vendido decrescente."""
        inv_with_products.sell_product("Caderno A4", quantity=10)
        inv_with_products.sell_product("Caneta Azul", quantity=3)
        report = inv_with_products.turnover_report()
        assert report[0]["name"] == "Caderno A4"

    def test_turnover_report_calculates_value(self, inv: Inventory) -> None:
        """Relatório calcula corretamente o valor total vendido."""
        inv.add_product("Item", quantity=100, min_stock=5, unit_price=10.00)
        inv.sell_product("Item", quantity=7)
        report = inv.turnover_report()
        assert report[0]["total_value_sold"] == test_inventory.approx(70.00)


# ─── Testes: serialização ────────────────────────────────────────────────────


class TestSerialization:
    def test_roundtrip_to_from_dict(self, inv_with_products: Inventory) -> None:
        """Serialização e desserialização preservam todos os dados."""
        data = inv_with_products.to_dict()
        restored = Inventory.from_dict(data)
        assert len(restored.list_products()) == len(inv_with_products.list_products())
        original = inv_with_products.get_product("Caneta Azul")
        restored_product = restored.get_product("Caneta Azul")
        assert original.quantity == restored_product.quantity
        assert original.unit_price == restored_product.unit_price
