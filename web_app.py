"""
web_app.py — Interface web do StockGuard para deploy no Render.

Expõe os dados do StockGuard via uma API REST simples (FastAPI),
permitindo acesso público ao inventário e aos fornecedores por link.

Endpoints:
  GET  /                    — Health check / info do sistema
  GET  /inventory           — Lista todos os produtos em estoque
  GET  /inventory/alerts    — Produtos abaixo do estoque mínimo
  GET  /inventory/report    — Relatório de giro (valor financeiro)
  GET  /suppliers           — Lista todos os fornecedores cadastrados
  POST /suppliers           — Cadastra fornecedor com busca de CEP (ViaCEP)
"""

from __future__ import annotations

import os

try:
    from fastapi import FastAPI, HTTPException
    from fastapi.responses import JSONResponse
    from pydantic import BaseModel
except ImportError as exc:
    raise ImportError(
        "FastAPI não instalado. Execute: pip install fastapi uvicorn"
    ) from exc

from stockguard.inventory import Inventory
from stockguard.storage import JSONStorage
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

# ─── Instância do inventário ─────────────────────────────────────────────────

_DATA_FILE = os.environ.get(
    "STOCKGUARD_DATA",
    os.path.join(os.path.expanduser("~"), ".stockguard", "inventory.json"),
)
_SUPPLIERS_FILE = os.environ.get(
    "STOCKGUARD_SUPPLIERS",
    os.path.join(os.path.expanduser("~"), ".stockguard", "suppliers.json"),
)

storage = JSONStorage(_DATA_FILE)
inventory = Inventory(storage)


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
    produtos = inventory.list_products()
    return {"total": len(produtos), "produtos": produtos}


@app.get("/inventory/alerts", tags=["Estoque"])
def get_alerts():
    """Retorna produtos com estoque abaixo do mínimo configurado."""
    todos = inventory.list_products()
    alertas = [p for p in todos if p["quantity"] < p.get("min_stock", 0)]
    return {"total_alertas": len(alertas), "alertas": alertas}


@app.get("/inventory/report", tags=["Estoque"])
def get_report():
    """Relatório de giro de mercadorias com valor financeiro."""
    produtos = inventory.list_products()
    relatorio = [
        {
            "produto": p["name"],
            "vendidos": p.get("sold", 0),
            "valor_vendido": round(p.get("sold", 0) * p.get("price", 0), 2),
            "estoque_atual": p["quantity"],
            "valor_estoque": round(p["quantity"] * p.get("price", 0), 2),
        }
        for p in produtos
    ]
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

    O campo `cep` pode ser informado com ou sem traço (ex: 01310-100 ou 01310100).
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