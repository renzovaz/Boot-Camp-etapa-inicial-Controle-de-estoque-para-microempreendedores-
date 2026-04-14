"""
test_suppliers_integration.py — Testes de integração do módulo de fornecedores.
"""

import json
import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from stockguard.suppliers import (
    buscar_endereco,
    adicionar_fornecedor,
    listar_fornecedores,
    formatar_endereco,
    CEPNotFoundError,
    CEPInvalidError,
    APIConnectionError,
    _limpar_cep,
)

# ─── Fixtures ────────────────────────────────────────────────────────────────

RESPOSTA_VIACEP_VALIDA = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "complemento": "de 1 a 610 - lado par",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP",
    "ibge": "3550308",
    "gia": "1004",
    "ddd": "11",
    "siafi": "7107",
}

RESPOSTA_CEP_NAO_ENCONTRADO = {"erro": True}


def _mock_requests_get(payload: dict, status: int = 200):
    """Cria um mock do requests.get que retorna payload como JSON."""
    mock_response = MagicMock()
    mock_response.json.return_value = payload
    mock_response.status_code = status
    return mock_response


# ─── Testes de validação de CEP (sem rede) ───────────────────────────────────

def test_limpar_cep_com_traco():
    assert _limpar_cep("01310-100") == "01310100"

def test_limpar_cep_sem_traco():
    assert _limpar_cep("01310100") == "01310100"

def test_limpar_cep_com_espacos():
    assert _limpar_cep("  01310 100  ") == "01310100"

def test_cep_invalido_letras():
    with pytest.raises(CEPInvalidError, match="inválido"):
        _limpar_cep("ABCDE-FGH")

def test_cep_invalido_curto():
    with pytest.raises(CEPInvalidError):
        _limpar_cep("1234567")

def test_cep_invalido_longo():
    with pytest.raises(CEPInvalidError):
        _limpar_cep("123456789")


# ─── Testes de buscar_endereco (mock da API) ──────────────────────────────────

@patch("stockguard.suppliers.requests.get")
def test_buscar_endereco_retorna_campos_corretos(mock_get):
    mock_get.return_value = _mock_requests_get(RESPOSTA_VIACEP_VALIDA)
    resultado = buscar_endereco("01310-100")

    assert resultado["logradouro"] == "Avenida Paulista"
    assert resultado["bairro"] == "Bela Vista"
    assert resultado["cidade"] == "São Paulo"
    assert resultado["estado"] == "SP"
    assert "01310" in resultado["cep"]


@patch("stockguard.suppliers.requests.get")
def test_buscar_endereco_cep_nao_encontrado(mock_get):
    mock_get.return_value = _mock_requests_get(RESPOSTA_CEP_NAO_ENCONTRADO)
    with pytest.raises(CEPNotFoundError, match="não encontrado"):
        buscar_endereco("00000000")


@patch("stockguard.suppliers.requests.get")
def test_buscar_endereco_sem_complemento(mock_get):
    resposta = {**RESPOSTA_VIACEP_VALIDA, "complemento": ""}
    mock_get.return_value = _mock_requests_get(resposta)
    resultado = buscar_endereco("01310100")
    assert resultado["complemento"] == ""


@patch("stockguard.suppliers.requests.get")
def test_buscar_endereco_erro_de_conexao(mock_get):
    from requests.exceptions import RequestException
    mock_get.side_effect = RequestException("Network unreachable")
    with pytest.raises(APIConnectionError):
        buscar_endereco("01310100")


# ─── Testes de formatar_endereco ─────────────────────────────────────────────

def test_formatar_endereco_completo():
    endereco = {
        "logradouro": "Avenida Paulista",
        "complemento": "andar 10",
        "bairro": "Bela Vista",
        "cidade": "São Paulo",
        "estado": "SP",
        "cep": "01310-100",
    }
    resultado = formatar_endereco(endereco)
    assert "Avenida Paulista" in resultado
    assert "São Paulo" in resultado
    assert "SP" in resultado
    assert "01310-100" in resultado


# ─── Testes de adicionar_fornecedor (mock + arquivo temporário) ───────────────

@patch("stockguard.suppliers.requests.get")
def test_adicionar_fornecedor_salva_arquivo(mock_get):
    mock_get.return_value = _mock_requests_get(RESPOSTA_VIACEP_VALIDA)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        caminho = tmp.name

    try:
        fornecedor = adicionar_fornecedor(
            "Papelaria Central", "01310-100", contato="(11) 9999-0000", caminho=caminho
        )
        assert fornecedor["nome"] == "Papelaria Central"
        assert fornecedor["endereco"]["cidade"] == "São Paulo"
        
        salvos = listar_fornecedores(caminho)
        assert len(salvos) == 1
        assert salvos[0]["nome"] == "Papelaria Central"
    finally:
        os.unlink(caminho)


# ─── Teste de integração REAL (requer internet) ───────────────────────────────

@pytest.mark.integration
def test_viacep_real_cep_conhecido():
    resultado = buscar_endereco("01310-100")
    assert resultado["cidade"].lower() == "são paulo"
    assert resultado["estado"] == "SP"


@pytest.mark.integration
def test_viacep_real_cep_inexistente():
    with pytest.raises(CEPNotFoundError):
        buscar_endereco("00000000")