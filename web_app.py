import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from stockguard.storage import Storage
from stockguard.suppliers import (
    adicionar_fornecedor,
    listar_fornecedores,
    CEPNotFoundError,
    CEPInvalidError,
    APIConnectionError,
)

app = FastAPI(
    title="StockGuard API",
    description="API do controle de estoque para a entrega intermediária",
    version="1.1.0",
)

arquivo_dados = os.environ.get("STOCKGUARD_DATA")
arquivo_fornecedores = os.environ.get(
    "STOCKGUARD_SUPPLIERS", 
    os.path.join(os.path.expanduser("~"), ".stockguard", "suppliers.json")
)

storage = Storage(filepath=arquivo_dados) if arquivo_dados else Storage()
inv = storage.load()

class FornecedorEntrada(BaseModel):
    nome: str
    cep: str
    contato: str = ""

@app.get("/")
def home():
    return {"status": "online", "projeto": "StockGuard", "docs": "/docs"}

@app.get("/inventory")
def listar_estoque():
    produtos = [
        {"nome": p.name, "quantidade": p.quantity, "minimo": p.min_stock, "preco": p.unit_price}
        for p in inv.list_products()
    ]
    return {"total": len(produtos), "produtos": produtos}

@app.get("/inventory/alerts")
def alertas_estoque():
    alertas = [
        {"nome": p.name, "quantidade": p.quantity, "minimo": p.min_stock}
        for p in inv.low_stock_alerts()
    ]
    return {"total_alertas": len(alertas), "alertas": alertas}

@app.get("/inventory/report")
def relatorio_giro():
    return {"relatorio": inv.turnover_report()}

@app.get("/suppliers")
def listar_fornecs():
    fornecedores = listar_fornecedores(arquivo_fornecedores)
    return {"total": len(fornecedores), "fornecedores": fornecedores}

@app.post("/suppliers", status_code=201)
def criar_fornecedor(dados: FornecedorEntrada):
    try:
        fornecedor = adicionar_fornecedor(
            dados.nome, dados.cep, contato=dados.contato, caminho=arquivo_fornecedores
        )
        return {"mensagem": "salvo com sucesso", "fornecedor": fornecedor}
    except CEPInvalidError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except CEPNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except APIConnectionError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))