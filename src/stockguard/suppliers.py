"""
suppliers.py — Módulo de cadastro de fornecedores com integração ViaCEP.

Fluxo:
  1. Usuário informa nome do fornecedor e CEP.
  2. A aplicação consulta a API pública ViaCEP (https://viacep.com.br).
  3. O endereço completo é preenchido automaticamente e salvo no JSON local.
"""

from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

VIACEP_URL = "https://viacep.com.br/ws/{cep}/json/"

_SUPPLIERS_FILE = os.path.join(os.path.expanduser("~"), ".stockguard", "suppliers.json")


# ─── Exceções ────────────────────────────────────────────────────────────────


class CEPNotFoundError(Exception):
    """CEP não encontrado na base ViaCEP."""


class CEPInvalidError(ValueError):
    """CEP com formato inválido."""


class APIConnectionError(OSError):
    """Falha de conexão com a API ViaCEP."""


# ─── Validação e consulta ────────────────────────────────────────────────────


def _limpar_cep(cep: str) -> str:
    """Remove traços e espaços e valida o formato do CEP."""
    cep = cep.strip().replace("-", "").replace(" ", "")
    if not cep.isdigit() or len(cep) != 8:
        raise CEPInvalidError(f"CEP '{cep}' inválido. Informe 8 dígitos numéricos (ex: 01310-100).")
    return cep


def buscar_endereco(cep: str, timeout: int = 5) -> dict:
    """
    Consulta a API ViaCEP e retorna o endereço como dicionário.

    Args:
        cep: CEP com ou sem traço (ex: '01310-100' ou '01310100').
        timeout: Segundos máximos de espera pela resposta.

    Returns:
        Dicionário com: cep, logradouro, bairro, cidade, estado, complemento.

    Raises:
        CEPInvalidError: CEP com formato inválido.
        CEPNotFoundError: CEP inexistente na base ViaCEP.
        APIConnectionError: Falha de rede ao acessar o serviço.
    """
    cep_limpo = _limpar_cep(cep)
    url = VIACEP_URL.format(cep=cep_limpo)

    try:
        with urlopen(url, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        raise APIConnectionError(f"Erro HTTP ao consultar ViaCEP: {exc.code} {exc.reason}") from exc
    except URLError as exc:
        raise APIConnectionError(
            f"Não foi possível conectar ao ViaCEP. Verifique sua internet. ({exc.reason})"
        ) from exc

    if data.get("erro"):
        raise CEPNotFoundError(f"CEP '{cep_limpo}' não encontrado na base ViaCEP.")

    return {
        "cep": data.get("cep", cep_limpo),
        "logradouro": data.get("logradouro", ""),
        "bairro": data.get("bairro", ""),
        "cidade": data.get("localidade", ""),
        "estado": data.get("uf", ""),
        "complemento": data.get("complemento", ""),
    }


def formatar_endereco(endereco: dict) -> str:
    """Formata o dicionário de endereço em string legível."""
    partes = [endereco["logradouro"]]
    if endereco.get("complemento"):
        partes.append(endereco["complemento"])
    partes.append(endereco["bairro"])
    partes.append(f"{endereco['cidade']}/{endereco['estado']}")
    partes.append(f"CEP {endereco['cep']}")
    return " — ".join(p for p in partes if p)


# ─── Persistência ────────────────────────────────────────────────────────────


def _carregar_fornecedores(caminho: str = _SUPPLIERS_FILE) -> list[dict]:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    if not os.path.exists(caminho):
        return []
    with open(caminho, encoding="utf-8") as f:
        content = f.read().strip()
    if not content:
        return []
    return json.loads(content)


def _salvar_fornecedores(fornecedores: list[dict], caminho: str = _SUPPLIERS_FILE) -> None:
    os.makedirs(os.path.dirname(caminho), exist_ok=True)
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(fornecedores, f, ensure_ascii=False, indent=2)


def adicionar_fornecedor(
    nome: str,
    cep: str,
    contato: str = "",
    caminho: str = _SUPPLIERS_FILE,
    timeout: int = 5,
) -> dict:
    """
    Cadastra um fornecedor consultando o endereço via ViaCEP.

    Raises:
        ValueError: Se o nome for vazio.
        CEPInvalidError: Se o CEP for malformado.
        CEPNotFoundError: Se o CEP não existir.
        APIConnectionError: Se a API estiver inacessível.
    """
    nome = nome.strip()
    if not nome:
        raise ValueError("O nome do fornecedor não pode ser vazio.")

    endereco = buscar_endereco(cep, timeout=timeout)
    fornecedores = _carregar_fornecedores(caminho)
    fornecedor = {
        "nome": nome,
        "contato": contato.strip(),
        "endereco": endereco,
    }
    fornecedores.append(fornecedor)
    _salvar_fornecedores(fornecedores, caminho)
    return fornecedor


def listar_fornecedores(caminho: str = _SUPPLIERS_FILE) -> list[dict]:
    """Retorna todos os fornecedores cadastrados."""
    return _carregar_fornecedores(caminho)
