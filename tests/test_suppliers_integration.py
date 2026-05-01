"""
test_suppliers_integration.py — Testes de integração do módulo de fornecedores.

Estratégia:
  - Testes com mock (padrão): simulam respostas da API — rodam offline no CI.
  - Testes reais (@pytest.mark.integration): fazem requisição real ao ViaCEP.
    Execute com: pytest -m integration tests/test_suppliers_integration.py
"""

from __future__ import annotations

import json
import os
import tempfile
from unittest.mock import MagicMock, patch

import pytest

from stockguard.suppliers import (
    APIConnectionError,
    CEPInvalidError,
    CEPNotFoundError,
    _limpar_cep,
    adicionar_fornecedor,
    buscar_endereco,
    formatar_endereco,
    listar_fornecedores,
)


# ─── Fixtures ────────────────────────────────────────────────────────────────

RESPOSTA_VIACEP_VALIDA = {
    "cep": "01310-100",
    "logradouro": "Avenida Paulista",
    "complemento": "de 1 a 610 - lado par",
    "bairro": "Bela Vista",
    "localidade": "São Paulo",
    "uf": "SP",
}

RESPOSTA_CEP_NAO_ENCONTRADO = {"erro": True}


def _mock_urlopen(payload: dict):
    mock_response = MagicMock()
    mock_response.read.return_value = json.dumps(payload).encode("utf-8")
    mock_response.__enter__ = lambda s: s
    mock_response.__exit__ = MagicMock(return_value=False)
    return mock_response


# ─── Validação de CEP (sem rede) ─────────────────────────────────────────────

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


# ─── buscar_endereco com mock ─────────────────────────────────────────────────

@patch("stockguard.suppliers.urlopen")
def test_buscar_endereco_retorna_campos_corretos(mock_urlopen):
    """Caminho feliz: API retorna endereço válido."""
    mock_urlopen.return_value = _mock_urlopen(RESPOSTA_VIACEP_VALIDA)
    resultado = buscar_endereco("01310-100")
    assert resultado["logradouro"] == "Avenida Paulista"
    assert resultado["bairro"] == "Bela Vista"
    assert resultado["cidade"] == "São Paulo"
    assert resultado["estado"] == "SP"
    assert "01310" in resultado["cep"]


@patch("stockguard.suppliers.urlopen")
def test_buscar_endereco_cep_nao_encontrado(mock_urlopen):
    """API retorna erro=true para CEP inexistente."""
    mock_urlopen.return_value = _mock_urlopen(RESPOSTA_CEP_NAO_ENCONTRADO)
    with pytest.raises(CEPNotFoundError, match="não encontrado"):
        buscar_endereco("00000000")


@patch("stockguard.suppliers.urlopen")
def test_buscar_endereco_sem_complemento(mock_urlopen):
    """Caso limite: endereço sem complemento deve funcionar normalmente."""
    resposta = {**RESPOSTA_VIACEP_VALIDA, "complemento": ""}
    mock_urlopen.return_value = _mock_urlopen(resposta)
    resultado = buscar_endereco("01310100")
    assert resultado["complemento"] == ""


@patch("stockguard.suppliers.urlopen")
def test_buscar_endereco_erro_de_conexao(mock_urlopen):
    """Simula falha de rede — deve lançar APIConnectionError."""
    from urllib.error import URLError
    mock_urlopen.side_effect = URLError("Network unreachable")
    with pytest.raises(APIConnectionError):
        buscar_endereco("01310100")


# ─── formatar_endereco ────────────────────────────────────────────────────────

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


def test_formatar_endereco_sem_complemento():
    endereco = {
        "logradouro": "Rua das Flores",
        "complemento": "",
        "bairro": "Centro",
        "cidade": "Curitiba",
        "estado": "PR",
        "cep": "80010-000",
    }
    resultado = formatar_endereco(endereco)
    assert "Curitiba" in resultado
    assert "PR" in resultado


# ─── adicionar_fornecedor com mock + arquivo temporário ──────────────────────

@patch("stockguard.suppliers.urlopen")
def test_adicionar_fornecedor_salva_arquivo(mock_urlopen):
    """Caminho feliz: fornecedor é salvo corretamente."""
    mock_urlopen.return_value = _mock_urlopen(RESPOSTA_VIACEP_VALIDA)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        caminho = tmp.name
    try:
        fornecedor = adicionar_fornecedor(
            "Papelaria Central", "01310-100", contato="(11) 9999-0000", caminho=caminho
        )
        assert fornecedor["nome"] == "Papelaria Central"
        assert fornecedor["endereco"]["cidade"] == "São Paulo"
        assert fornecedor["contato"] == "(11) 9999-0000"
        salvos = listar_fornecedores(caminho)
        assert len(salvos) == 1
        assert salvos[0]["nome"] == "Papelaria Central"
    finally:
        os.unlink(caminho)


@patch("stockguard.suppliers.urlopen")
def test_adicionar_multiplos_fornecedores(mock_urlopen):
    """Múltiplos fornecedores devem ser acumulados."""
    mock_urlopen.return_value = _mock_urlopen(RESPOSTA_VIACEP_VALIDA)
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        caminho = tmp.name
    try:
        adicionar_fornecedor("Fornecedor A", "01310100", caminho=caminho)
        adicionar_fornecedor("Fornecedor B", "01310100", caminho=caminho)
        salvos = listar_fornecedores(caminho)
        assert len(salvos) == 2
    finally:
        os.unlink(caminho)


def test_adicionar_fornecedor_nome_vazio():
    with pytest.raises(ValueError, match="nome do fornecedor"):
        adicionar_fornecedor("   ", "01310100")


def test_adicionar_fornecedor_cep_invalido():
    with pytest.raises(CEPInvalidError):
        adicionar_fornecedor("Fornecedor X", "123")


# ─── Testes de integração REAL (requer internet) ──────────────────────────────

@pytest.mark.integration
def test_viacep_real_cep_conhecido():
    """Integração real com ViaCEP. Execute: pytest -m integration"""
    resultado = buscar_endereco("01310-100")
    assert resultado["cidade"].lower() == "são paulo"
    assert resultado["estado"] == "SP"
    assert resultado["logradouro"] != ""


@pytest.mark.integration
def test_viacep_real_cep_inexistente():
    """Integração real: CEP inexistente deve lançar CEPNotFoundError."""
    with pytest.raises(CEPNotFoundError):
        buscar_endereco("00000000")