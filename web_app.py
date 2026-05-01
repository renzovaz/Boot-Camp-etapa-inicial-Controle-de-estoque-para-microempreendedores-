"""
web_app.py — Interface web do StockGuard para deploy no Render.

Versão corrigida: não depende de Inventory/Storage — lê o arquivo JSON
diretamente, compatível com qualquer estrutura do projeto.

Endpoints:
  GET  /                    — Health check / info do sistema
  GET  /inventory           — Lista todos os produtos em estoque
  GET  /inventory/alerts    — Produtos abaixo do estoque mínimo
  GET  /inventory/report    — Relatório financeiro do estoque
  GET  /suppliers           — Lista todos os fornecedores cadastrados
  POST /suppliers           — Cadastra fornecedor com busca de CEP (ViaCEP)
"""

from __future__ import annotations

import json
import os

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from stockguard.suppliers import (
    adicionar_fornecedor,
    listar_fornecedores,
    CEPNotFoundError,
    CEPInvalidError,
    APIConnectionError,
)

app = FastAPI(
    title="StockGuard API",
    description="Controle de estoque para microempreendedores — StockGuard",
    version="1.1.0",
)

# ─── Caminhos dos arquivos de dados ──────────────────────────────────────────

_DATA_FILE = os.environ.get(
    "STOCKGUARD_DATA",
    os.path.join(os.path.expanduser("~"), ".stockguard", "inventory.json"),
)
_SUPPLIERS_FILE = os.environ.get(
    "STOCKGUARD_SUPPLIERS",
    os.path.join(os.path.expanduser("~"), ".stockguard", "suppliers.json"),
)


def _ler_inventario() -> list[dict]:
    """Lê o inventário direto do arquivo JSON, sem depender de classes internas."""
    if not os.path.exists(_DATA_FILE):
        return []
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        dados = json.load(f)
    # Suporta tanto {"products": [...]} quanto {"produtos": [...]} quanto lista direta
    if isinstance(dados, list):
        return dados
    return dados.get("products", dados.get("produtos", []))


# ─── Modelos Pydantic ────────────────────────────────────────────────────────

class SupplierIn(BaseModel):
    nome: str
    cep: str
    contato: str = ""


# ─── Rotas ───────────────────────────────────────────────────────────────────

@app.get("/", tags=["Sistema"])
def root():
    """Health check e informações básicas do sistema."""
    return {
        "app": "StockGuard",
        "version": "1.1.0",
        "status": "online",
        "docs": "/docs",
    }


@app.get("/inventory", tags=["Estoque"])
def get_inventory():
    """Lista todos os produtos em estoque."""
    produtos = _ler_inventario()
    return {"total": len(produtos), "produtos": produtos}


@app.get("/inventory/alerts", tags=["Estoque"])
def get_alerts():
    """Retorna produtos com estoque abaixo do mínimo configurado."""
    todos = _ler_inventario()
    # Suporta tanto "quantity"/"min_stock" quanto "quantidade"/"estoque_minimo"
    alertas = [
        p for p in todos
        if p.get("quantity", p.get("quantidade", 0))
        < p.get("min_stock", p.get("estoque_minimo", 0))
    ]
    return {"total_alertas": len(alertas), "alertas": alertas}


@app.get("/inventory/report", tags=["Estoque"])
def get_report():
    """Relatório de giro de mercadorias com valor financeiro."""
    produtos = _ler_inventario()
    relatorio = []
    for p in produtos:
        nome = p.get("name", p.get("nome", ""))
        qtd = p.get("quantity", p.get("quantidade", 0))
        preco = p.get("price", p.get("preco", 0))
        vendidos = p.get("sold", p.get("vendidos", 0))
        relatorio.append({
            "produto": nome,
            "vendidos": vendidos,
            "valor_vendido": round(vendidos * preco, 2),
            "estoque_atual": qtd,
            "valor_estoque": round(qtd * preco, 2),
        })
    valor_total = sum(r["valor_estoque"] for r in relatorio)
    return {
        "valor_total_estoque": round(valor_total, 2),
        "produtos": relatorio,
    }


@app.get("/suppliers", tags=["Fornecedores"])
def get_suppliers():
    """Lista todos os fornecedores cadastrados."""
    fornecedores = listar_fornecedores(_SUPPLIERS_FILE)
    return {"total": len(fornecedores), "fornecedores": fornecedores}


@app.post("/suppliers", tags=["Fornecedores"], status_code=201)
def create_supplier(body: SupplierIn):
    """
    Cadastra um fornecedor com busca automática de endereço via ViaCEP.
    O campo cep pode ser com ou sem traço (ex: 01310-100 ou 01310100).
    """
    try:
        fornecedor = adicionar_fornecedor(
            body.nome, body.cep, contato=body.contato, caminho=_SUPPLIERS_FILE
        )
        return {"mensagem": "Fornecedor cadastrado com sucesso.", "fornecedor": fornecedor}
    except CEPInvalidError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CEPNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))