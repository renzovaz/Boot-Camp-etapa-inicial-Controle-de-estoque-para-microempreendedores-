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

# importando o comando do seu arquivo novo
# assumindo que a função principal lá do click se chama supplier
from stockguard.cli_suppliers import supplier

def _ok(msg: str) -> None:
    click.secho(f"✔  {msg}", fg="green")

def _warn(msg: str) -> None:
    click.secho(f"⚠  {msg}", fg="yellow")

def _err(msg: str) -> None:
    click.secho(f"✘  {msg}", fg="red", err=True)

def _header(title: str) -> None:
    click.secho(f"\n{title}", fg="cyan", bold=True)
    click.echo("─" * 50)

@click.group()
@click.option("--data", type=click.Path(path_type=Path), help="Caminho alternativo para o arquivo de dados")
@click.pass_context
def cli(ctx, data):
    """StockGuard — Controle de estoque para microempreendedores."""
    storage = Storage(filepath=data) if data else Storage()
    try:
        inv = storage.load()
    except Exception as exc:
        _err(f"Erro ao carregar dados: {exc}")
        sys.exit(1)
    ctx.obj = {"inv": inv, "storage": storage}

@cli.command(help="Cadastra ou repõe produto no estoque")
@click.argument("name")
@click.argument("quantity", type=int)
@click.option("--min-stock", "-m", type=int, default=5, help="Estoque mínimo para alerta")
@click.option("--price", "-p", type=float, default=0.0, help="Preço unitário em R$")
@click.pass_obj
def add(obj, name, quantity, min_stock, price):
    inv, storage = obj["inv"], obj["storage"]
    try:
        product = inv.add_product(name=name, quantity=quantity, min_stock=min_stock, unit_price=price)
        storage.save(inv)
        _ok(f"Produto '{product.name}' salvo — estoque: {product.quantity} unidades @ R$ {product.unit_price:.2f}")
        if product.quantity <= product.min_stock:
            _warn("Estoque já está no nível mínimo ou abaixo!")
    except Exception as exc:
        _err(str(exc))
        sys.exit(1)

@cli.command(help="Registra venda (baixa de estoque)")
@click.argument("name")
@click.argument("quantity", type=int)
@click.pass_obj
def sell(obj, name, quantity):
    inv, storage = obj["inv"], obj["storage"]
    try:
        product = inv.sell_product(name=name, quantity=quantity)
        storage.save(inv)
        total = quantity * product.unit_price
        _ok(f"Venda registrada: {quantity}× '{product.name}' = R$ {total:.2f}. Saldo: {product.quantity} unidades.")
        if product.quantity <= product.min_stock:
            _warn(f"ALERTA: '{product.name}' atingiu o estoque mínimo ({product.min_stock})!")
    except Exception as exc:
        _err(str(exc))
        sys.exit(1)

@cli.command(name="list", help="Lista todos os produtos em estoque")
@click.pass_obj
def list_products(obj):
    inv = obj["inv"]
    products = inv.list_products()
    if not products:
        click.echo("Nenhum produto cadastrado.")
        return

    _header("Estoque atual")
    fmt = "{:<28} {:>8} {:>8} {:>10}  {}"
    click.echo(fmt.format("Produto", "Qtd", "Mín", "Preço", "Status"))
    click.echo("─" * 70)
    for p in products:
        status = click.style("BAIXO", fg="red") if p.quantity <= p.min_stock else click.style("OK", fg="green")
        click.echo(fmt.format(p.name[:28], p.quantity, p.min_stock, f"R$ {p.unit_price:.2f}", status))
    click.echo(f"\nTotal: {len(products)} produto(s)")

@cli.command(help="Exibe produtos abaixo do estoque mínimo")
@click.pass_obj
def alerts(obj):
    inv = obj["inv"]
    low = inv.low_stock_alerts()
    if not low:
        _ok("Nenhum produto abaixo do estoque mínimo.")
        return

    _header(f"⚠  Alertas de estoque mínimo ({len(low)} produto(s))")
    for p in low:
        click.echo(f"  • {p.name}: {p.quantity} unid. (mín: {p.min_stock})")

@cli.command(help="Gera relatório de giro de mercadorias")
@click.pass_obj
def report(obj):
    inv = obj["inv"]
    report_data = inv.turnover_report()
    if not report_data:
        click.echo("Nenhum dado para gerar relatório.")
        return

    _header("Relatório de giro de mercadorias")
    fmt = "{:<28} {:>8} {:>10} {:>14}"
    click.echo(fmt.format("Produto", "Vendidos", "Val. vendido", "Estoque atual"))
    click.echo("─" * 68)
    for r in report_data:
        alert = click.style(" ⚠", fg="red") if r["below_min"] else ""
        click.echo(fmt.format(r["name"][:28], r["total_sold"], f"R$ {r['total_value_sold']:.2f}", f"R$ {r['current_stock_value']:.2f}") + alert)

@cli.command(help="Remove produto do inventário")
@click.argument("name")
@click.pass_obj
def remove(obj, name):
    inv, storage = obj["inv"], obj["storage"]
    try:
        product = inv.remove_product(name=name)
        storage.save(inv)
        _ok(f"Produto '{product.name}' removido do inventário.")
    except Exception as exc:
        _err(str(exc))
        sys.exit(1)

# conectando o comando que veio do seu outro arquivo
cli.add_command(supplier)

def main():
    cli()

if __name__ == "__main__":
    main()