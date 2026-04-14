"""Interface de linha de comando do StockGuard.

Uso: stockguard <comando> [opções]
"""

from __future__ import annotations

import sys
from pathlib import Path

import click

from stockguard.inventory import (
    InvalidQuantityError,
    Inventory,
    InventoryError,
    ProductNotFoundError,
)
from stockguard.storage import Storage

# ─── Cores / helpers ─────────────────────────────────────────────────────────

def _ok(msg: str) -> None:
    click.echo(click.style("✔", fg="green") + f"  {msg}")


def _warn(msg: str) -> None:
    click.echo(click.style("⚠", fg="yellow") + f"  {msg}")


def _err(msg: str) -> None:
    click.echo(click.style("✘", fg="red") + f"  {msg}", err=True)


def _header(title: str) -> None:
    click.echo(f"\n{click.style(title, fg='cyan', bold=True)}")
    click.echo("─" * 50)


# ─── Contexto compartilhado ──────────────────────────────────────────────────

class AppContext:
    """Carrega e expõe Inventory + Storage para todos os sub-comandos."""

    def __init__(self, data: Path | None) -> None:
        self.storage = Storage(filepath=data) if data else Storage()
        try:
            self.inv: Inventory = self.storage.load()
        except Exception as exc:
            _err(f"Erro ao carregar dados: {exc}")
            sys.exit(1)

    def save(self) -> None:
        try:
            self.storage.save(self.inv)
        except Exception as exc:
            _err(f"Erro ao salvar dados: {exc}")
            sys.exit(1)


pass_ctx = click.make_pass_decorator(AppContext)


# ─── Grupo principal ─────────────────────────────────────────────────────────

@click.group(
    context_settings={"help_option_names": ["-h", "--help"]},
)
@click.option(
    "--data",
    metavar="ARQUIVO",
    type=click.Path(dir_okay=False, path_type=Path),
    default=None,
    help="Caminho alternativo para o arquivo de dados (padrão: ~/.stockguard/inventory.json).",
)
@click.version_option(package_name="stockguard", prog_name="stockguard")
@click.pass_context
def cli(ctx: click.Context, data: Path | None) -> None:
    """StockGuard — Controle de estoque para microempreendedores.

    Automatiza baixas, emite alertas de estoque mínimo e gera métricas
    de giro de mercadorias.
    """
    ctx.obj = AppContext(data)
    ctx.call_on_close(ctx.obj.save)


# ─── Comandos ────────────────────────────────────────────────────────────────

@cli.command("add")
@click.argument("nome")
@click.argument("quantidade", type=int)
@click.option("--min-stock", "-m", default=5, show_default=True, metavar="MIN",
              help="Estoque mínimo para alerta.")
@click.option("--price", "-p", default=0.0, show_default=True, metavar="PRECO",
              help="Preço unitário em R$.")
@pass_ctx
def cmd_add(app: AppContext, nome: str, quantidade: int, min_stock: int, price: float) -> None:
    """Cadastra ou repõe produto no estoque.

    Exemplo:

        stockguard add "Caneta Azul" 50 --min-stock 10 --price 1.50
    """
    try:
        product = app.inv.add_product(
            name=nome,
            quantity=quantidade,
            min_stock=min_stock,
            unit_price=price,
        )
    except (InvalidQuantityError, InventoryError) as exc:
        _err(str(exc))
        sys.exit(1)

    _ok(
        f"Produto '{product.name}' salvo — "
        f"estoque: {product.quantity} unidades "
        f"@ R$ {product.unit_price:.2f}"
    )
    if product.quantity <= product.min_stock:
        _warn("Estoque já está no nível mínimo ou abaixo!")


@cli.command("sell")
@click.argument("nome")
@click.argument("quantidade", type=int)
@pass_ctx
def cmd_sell(app: AppContext, nome: str, quantidade: int) -> None:
    """Registra venda e dá baixa no estoque.

    Exemplo:

        stockguard sell "Caneta Azul" 5
    """
    try:
        product = app.inv.sell_product(name=nome, quantity=quantidade)
    except (InvalidQuantityError, ProductNotFoundError) as exc:
        _err(str(exc))
        sys.exit(1)
    except InventoryError as exc:
        _err(f"Erro de estoque: {exc}")
        sys.exit(1)

    total = quantidade * product.unit_price
    _ok(
        f"Venda registrada: {quantidade}× '{product.name}' "
        f"= R$ {total:.2f}. Saldo: {product.quantity} unidades."
    )
    if product.quantity <= product.min_stock:
        _warn(f"ALERTA: '{product.name}' atingiu o estoque mínimo ({product.min_stock})!")


@cli.command("list")
@pass_ctx
def cmd_list(app: AppContext) -> None:
    """Lista todos os produtos em estoque."""
    products = app.inv.list_products()
    if not products:
        click.echo("Nenhum produto cadastrado.")
        return

    _header("Estoque atual")
    fmt = "{:<28} {:>8} {:>8} {:>10}  {}"
    click.echo(fmt.format("Produto", "Qtd", "Mín", "Preço", "Status"))
    click.echo("─" * 70)

    for p in products:
        if p.quantity <= p.min_stock:
            status = click.style("BAIXO", fg="red")
        else:
            status = click.style("OK", fg="green")

        click.echo(
            fmt.format(
                p.name[:28],
                p.quantity,
                p.min_stock,
                f"R$ {p.unit_price:.2f}",
                status,
            )
        )

    click.echo(f"\nTotal: {len(products)} produto(s)")


@cli.command("alerts")
@pass_ctx
def cmd_alerts(app: AppContext) -> None:
    """Exibe produtos abaixo do estoque mínimo."""
    low = app.inv.low_stock_alerts()
    if not low:
        _ok("Nenhum produto abaixo do estoque mínimo.")
        return

    _header(f"⚠  Alertas de estoque mínimo ({len(low)} produto(s))")
    for p in low:
        bullet = click.style("•", fg="red")
        click.echo(f"  {bullet} {p.name}: {p.quantity} unid. (mín: {p.min_stock})")


@cli.command("report")
@pass_ctx
def cmd_report(app: AppContext) -> None:
    """Gera relatório de giro de mercadorias."""
    report = app.inv.turnover_report()
    if not report:
        click.echo("Nenhum dado para gerar relatório.")
        return

    _header("Relatório de giro de mercadorias")
    fmt = "{:<28} {:>8} {:>10} {:>14}"
    click.echo(fmt.format("Produto", "Vendidos", "Val. vendido", "Estoque atual"))
    click.echo("─" * 68)

    for r in report:
        alert = f" {click.style('⚠', fg='red')}" if r["below_min"] else ""
        click.echo(
            fmt.format(
                r["name"][:28],
                r["total_sold"],
                f"R$ {r['total_value_sold']:.2f}",
                f"R$ {r['current_stock_value']:.2f}",
            )
            + alert
        )


@cli.command("remove")
@click.argument("nome")
@click.confirmation_option(
    "--yes",
    prompt="Tem certeza que deseja remover este produto?",
)
@pass_ctx
def cmd_remove(app: AppContext, nome: str) -> None:
    """Remove um produto do inventário.

    Exemplo:

        stockguard remove "Caneta Azul"
    """
    try:
        product = app.inv.remove_product(name=nome)
    except ProductNotFoundError as exc:
        _err(str(exc))
        sys.exit(1)

    _ok(f"Produto '{product.name}' removido do inventário.")


# ─── Integração com sub-grupo de fornecedores ─────────────────────────────────

from stockguard.cli_suppliers import supplier  # noqa: E402
cli.add_command(supplier)


# ─── Entrypoint ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()