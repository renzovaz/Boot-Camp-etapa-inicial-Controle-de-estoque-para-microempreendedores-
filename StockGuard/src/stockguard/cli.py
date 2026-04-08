"""Interface de linha de comando do StockGuard.

Uso: stockguard <comando> [opções]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from stockguard.inventory import (
    Inventory,
    InventoryError,
    InvalidQuantityError,
    ProductNotFoundError,
)
from stockguard.storage import Storage

_RESET = "\033[0m"
_BOLD = "\033[1m"
_RED = "\033[31m"
_GREEN = "\033[32m"
_YELLOW = "\033[33m"
_CYAN = "\033[36m"


def _ok(msg: str) -> None:
    print(f"{_GREEN}✔{_RESET}  {msg}")


def _warn(msg: str) -> None:
    print(f"{_YELLOW}⚠{_RESET}  {msg}")


def _err(msg: str) -> None:
    print(f"{_RED}✘{_RESET}  {msg}", file=sys.stderr)


def _header(title: str) -> None:
    print(f"\n{_BOLD}{_CYAN}{title}{_RESET}")
    print("─" * 50)


def cmd_add(args: argparse.Namespace, inv: Inventory) -> None:
    product = inv.add_product(
        name=args.name,
        quantity=args.quantity,
        min_stock=args.min_stock,
        unit_price=args.price,
    )
    _ok(
        f"Produto '{product.name}' salvo — "
        f"estoque: {product.quantity} unidades "
        f"@ R$ {product.unit_price:.2f}"
    )
    if product.quantity <= product.min_stock:
        _warn("Estoque já está no nível mínimo ou abaixo!")


def cmd_sell(args: argparse.Namespace, inv: Inventory) -> None:
    product = inv.sell_product(name=args.name, quantity=args.quantity)
    total = args.quantity * product.unit_price
    _ok(
        f"Venda registrada: {args.quantity}× '{product.name}' "
        f"= R$ {total:.2f}. Saldo: {product.quantity} unidades."
    )
    if product.quantity <= product.min_stock:
        _warn(f"ALERTA: '{product.name}' atingiu o estoque mínimo ({product.min_stock})!")


def cmd_list(args: argparse.Namespace, inv: Inventory) -> None:  # noqa: ARG001
    products = inv.list_products()
    if not products:
        print("Nenhum produto cadastrado.")
        return

    _header("Estoque atual")
    fmt = "{:<28} {:>8} {:>8} {:>10}  {}"
    print(fmt.format("Produto", "Qtd", "Mín", "Preço", "Status"))
    print("─" * 70)
    for p in products:
        status = f"{_RED}BAIXO{_RESET}" if p.quantity <= p.min_stock else f"{_GREEN}OK{_RESET}"
        print(
            fmt.format(
                p.name[:28],
                p.quantity,
                p.min_stock,
                f"R$ {p.unit_price:.2f}",
                status,
            )
        )
    print(f"\nTotal: {len(products)} produto(s)")


def cmd_alerts(args: argparse.Namespace, inv: Inventory) -> None:  # noqa: ARG001
    low = inv.low_stock_alerts()
    if not low:
        _ok("Nenhum produto abaixo do estoque mínimo.")
        return

    _header(f"⚠  Alertas de estoque mínimo ({len(low)} produto(s))")
    for p in low:
        print(f"  {_RED}•{_RESET} {p.name}: {p.quantity} unid. (mín: {p.min_stock})")


def cmd_report(args: argparse.Namespace, inv: Inventory) -> None:  # noqa: ARG001
    report = inv.turnover_report()
    if not report:
        print("Nenhum dado para gerar relatório.")
        return

    _header("Relatório de giro de mercadorias")
    fmt = "{:<28} {:>8} {:>10} {:>14}"
    print(fmt.format("Produto", "Vendidos", "Val. vendido", "Estoque atual"))
    print("─" * 68)
    for r in report:
        alert = f" {_RED}⚠{_RESET}" if r["below_min"] else ""
        print(
            fmt.format(
                r["name"][:28],
                r["total_sold"],
                f"R$ {r['total_value_sold']:.2f}",
                f"R$ {r['current_stock_value']:.2f}",
            )
            + alert
        )


def cmd_remove(args: argparse.Namespace, inv: Inventory) -> None:
    product = inv.remove_product(name=args.name)
    _ok(f"Produto '{product.name}' removido do inventário.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="stockguard",
        description=(
            "StockGuard — Controle de estoque para microempreendedores.\n"
            "Automatiza baixas, emite alertas de estoque mínimo e gera "
            "métricas de giro de mercadorias."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--data",
        metavar="ARQUIVO",
        type=Path,
        help="Caminho alternativo para o arquivo de dados (padrão: ~/.stockguard/inventory.json)",
    )

    sub = parser.add_subparsers(dest="command", title="Comandos disponíveis")
    sub.required = True

    # add
    p_add = sub.add_parser("add", help="Cadastra ou repõe produto no estoque")
    p_add.add_argument("name", metavar="NOME", help="Nome do produto")
    p_add.add_argument("quantity", metavar="QTD", type=int, help="Quantidade a adicionar")
    p_add.add_argument(
        "--min-stock", "-m", metavar="MIN", type=int, default=5,
        help="Estoque mínimo para alerta (padrão: 5)"
    )
    p_add.add_argument(
        "--price", "-p", metavar="PRECO", type=float, default=0.0,
        help="Preço unitário em R$ (padrão: 0.00)"
    )

    # sell
    p_sell = sub.add_parser("sell", help="Registra venda (baixa de estoque)")
    p_sell.add_argument("name", metavar="NOME", help="Nome do produto")
    p_sell.add_argument("quantity", metavar="QTD", type=int, help="Quantidade vendida")

    # list
    sub.add_parser("list", help="Lista todos os produtos em estoque")

    # alerts
    sub.add_parser("alerts", help="Exibe produtos abaixo do estoque mínimo")

    # report
    sub.add_parser("report", help="Gera relatório de giro de mercadorias")

    # remove
    p_remove = sub.add_parser("remove", help="Remove produto do inventário")
    p_remove.add_argument("name", metavar="NOME", help="Nome do produto a remover")

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    storage = Storage(filepath=args.data) if args.data else Storage()

    try:
        inv = storage.load()
    except Exception as exc:
        _err(f"Erro ao carregar dados: {exc}")
        return 1

    dispatch = {
        "add": cmd_add,
        "sell": cmd_sell,
        "list": cmd_list,
        "alerts": cmd_alerts,
        "report": cmd_report,
        "remove": cmd_remove,
    }

    try:
        dispatch[args.command](args, inv)
    except (InvalidQuantityError, ProductNotFoundError) as exc:
        _err(str(exc))
        return 1
    except InventoryError as exc:
        _err(f"Erro de estoque: {exc}")
        return 1

    try:
        storage.save(inv)
    except Exception as exc:
        _err(f"Erro ao salvar dados: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())