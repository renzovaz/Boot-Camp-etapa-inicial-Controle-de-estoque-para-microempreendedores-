# StockGuard 🛡️

[![CI](https://github.com/renzovaz/Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-/actions/workflows/ci.yml/badge.svg?branch=entrega-intermediaria)](https://github.com/renzovaz/Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-/actions/workflows/ci.yml)
![Versão](https://img.shields.io/badge/versão-1.1.0-blue)
![Python](https://img.shields.io/badge/python-3.10+-green)
![Licença](https://img.shields.io/badge/licença-GPL--3.0-lightgrey)

> Controle de estoque para microempreendedores — automatiza baixas em tempo real, dispara alertas de estoque mínimo e gera métricas de giro de mercadorias.

---

## 🌐 Deploy — Aplicação Online

| | Link |
|---|---|
| **API** | https://boot-camp-etapa-inicial-controle-de.onrender.com |
| **Documentação interativa** | https://boot-camp-etapa-inicial-controle-de.onrender.com/docs |

---

## 🎯 O Problema

Microempreendedores — donos de papelarias, mercearias, bazares, depósitos — perdem dinheiro todo dia por falta de controle de estoque. Sem saber o que acabou, quando repor ou o que mais vende, decisões erradas viram prejuízo: falta de produto na hora da venda, compras desnecessárias que imobilizam caixa, e perdas por vencimento ou obsolescência.

## 💡 A Solução

O **StockGuard** é uma ferramenta CLI leve, que roda diretamente no terminal, sem precisar de servidor. Ela permite:

- Cadastrar e repor produtos no estoque
- Registrar vendas (baixas automáticas)
- Receber alertas quando o estoque cai abaixo do mínimo definido
- Visualizar relatório de giro de mercadorias com valor financeiro
- Remover produtos do inventário
- **Cadastrar fornecedores com endereço preenchido automaticamente via CEP** *(novo — v1.1.0)*

Os dados ficam salvos localmente em `~/.stockguard/`, sem necessidade de banco de dados externo.

## 👥 Público-alvo

Microempreendedores individuais (MEI) e pequenos negócios que precisam de controle simples, rápido e confiável de inventário.

---

## ✨ Funcionalidades

### CLI — Estoque

| Comando | O que faz |
|---|---|
| `stockguard add NOME QTD` | Cadastra ou repõe produto |
| `stockguard sell NOME QTD` | Registra venda (baixa automática) |
| `stockguard list` | Lista todos os produtos com status |
| `stockguard alerts` | Exibe produtos abaixo do estoque mínimo |
| `stockguard report` | Relatório de giro com valor financeiro |
| `stockguard remove NOME` | Remove produto do inventário |

### CLI — Fornecedores *(novo — v1.1.0)*

| Comando | O que faz |
|---|---|
| `stockguard supplier add NOME CEP` | Cadastra fornecedor com endereço via ViaCEP |
| `stockguard supplier list` | Lista todos os fornecedores cadastrados |

### API REST — Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/` | Health check |
| GET | `/inventory` | Lista produtos em estoque |
| GET | `/inventory/alerts` | Alertas de estoque mínimo |
| GET | `/inventory/report` | Relatório de giro financeiro |
| GET | `/suppliers` | Lista fornecedores |
| POST | `/suppliers` | Cadastra fornecedor via CEP (ViaCEP) |

---

## 🔗 Integração com ViaCEP *(novo — v1.1.0)*

O StockGuard agora permite cadastrar fornecedores com endereço preenchido automaticamente via CEP, consumindo a API pública [ViaCEP](https://viacep.com.br).

```bash
# Cadastrar fornecedor — endereço preenchido automaticamente
stockguard supplier add "Papelaria Central" 01310-100
# 🔍 Consultando endereço para o CEP 01310-100...
# ✔  Fornecedor 'Papelaria Central' cadastrado.
#    Endereço: Avenida Paulista — Bela Vista — São Paulo/SP — CEP 01310-100

# Com contato
stockguard supplier add "Distribuidora XYZ" 20040-020 --contato "(21) 9999-0000"

# Listar fornecedores
stockguard supplier list
```

---

## 🛠️ Tecnologias Utilizadas

| Tecnologia | Finalidade |
|---|---|
| Python 3.10+ | Linguagem principal |
| `click` | Interface CLI |
| `fastapi` + `uvicorn` | API REST para deploy |
| `urllib` (stdlib) | Integração com ViaCEP |
| `pytest` + `pytest-cov` | Testes automatizados |
| `ruff` | Linting e formatação |
| GitHub Actions | Integração Contínua (CI) |
| Render | Deploy em nuvem |

---

## 📁 Estrutura do Projeto

```
Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-/
├── .github/
│   └── workflows/
│       └── ci.yml                  # Pipeline CI — lint + testes
├── src/
│   └── stockguard/
│       ├── __init__.py
│       ├── cli.py                  # Interface CLI principal
│       ├── cli_suppliers.py        # Comandos CLI de fornecedores (novo)
│       ├── inventory.py            # Lógica de estoque
│       ├── storage.py              # Persistência de dados
│       └── suppliers.py            # Integração ViaCEP (novo)
├── tests/
│   ├── __init__.py
│   ├── test_inventory.py           # Testes unitários de estoque
│   └── test_suppliers_integration.py  # Testes de integração ViaCEP (novo)
├── web_app.py                      # API REST para deploy (novo)
├── render.yaml                     # Configuração de deploy (novo)
├── conftest.py
├── .gitignore
├── CHANGELOG.md
├── LICENSE
├── pyproject.toml
└── README.md
```

---

## 🚀 Instalação

### Pré-requisitos

- Python 3.10 ou superior
- pip

### Instalar a partir do repositório

```bash
# Clone o repositório
git clone https://github.com/renzovaz/Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-
cd Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-

# Instale em modo editável (desenvolvimento)
pip install -e ".[dev]"
```

### Verificar a instalação

```bash
stockguard --help
```

---

## ▶️ Como Usar

### Cadastrar produto

```bash
stockguard add "Caneta Azul" 100 --min-stock 15 --price 1.50
# ✔  Produto 'Caneta Azul' salvo — estoque: 100 unidades @ R$ 1.50
```

### Registrar venda

```bash
stockguard sell "Caneta Azul" 20
# ✔  Venda registrada: 20× 'Caneta Azul' = R$ 30.00. Saldo: 80 unidades.
```

### Listar estoque

```bash
stockguard list
```

```
Estoque atual
──────────────────────────────────────────────────
Produto                          Qtd    Mín      Preço  Status
──────────────────────────────────────────────────────────────────────
Borracha                           8     15   R$ 0.80  BAIXO
Caderno A4                        20      5  R$ 12.00  OK
Caneta Azul                       80     15   R$ 1.50  OK
```

### Alertas de estoque mínimo

```bash
stockguard alerts
# ⚠  Alertas de estoque mínimo (1 produto(s))
#   • Borracha: 8 unid. (mín: 15)
```

### Relatório de giro

```bash
stockguard report
```

### Cadastrar fornecedor com CEP

```bash
stockguard supplier add "Papelaria Central" 01310-100
stockguard supplier list
```

---

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Com cobertura de código
pytest --cov=src --cov-report=term-missing

# Testes de integração real com ViaCEP (requer internet)
pytest -m integration tests/test_suppliers_integration.py -v
```

Os testes cobrem:
- Caminho feliz (operações corretas)
- Entradas inválidas (quantidade negativa, nome vazio, CEP inválido)
- Casos limite (vender exatamente o estoque disponível, arquivo JSON vazio)
- Alertas e relatórios
- Integração com ViaCEP via mock (offline) e real (online)

---

## 🔍 Linting

```bash
# Verificar erros e estilo
ruff check src/ tests/

# Verificar formatação
ruff format --check src/ tests/

# Corrigir automaticamente
ruff check --fix src/ tests/
ruff format src/ tests/
```

---

## ⚙️ CI com GitHub Actions

A pipeline executa automaticamente em todo `push` e `pull_request`:

1. Instala dependências
2. Verifica módulo `suppliers` (integração ViaCEP)
3. Executa `ruff check` (lint)
4. Executa `ruff format --check` (formatação)
5. Executa `pytest` com cobertura (testes unitários)
6. Executa testes de integração com mock do ViaCEP

Compatível com Python **3.10, 3.11 e 3.12**.

---

## ☁️ Deploy no Render

A API REST está publicada gratuitamente no Render:

- **URL:** https://boot-camp-etapa-inicial-controle-de.onrender.com
- **Docs:** https://boot-camp-etapa-inicial-controle-de.onrender.com/docs

Para fazer seu próprio deploy:

1. Acesse [render.com](https://render.com) → New → Web Service
2. Conecte o repositório GitHub
3. Configure:
   - **Branch:** `entrega-intermediaria`
   - **Build Command:** `pip install -e ".[web]"`
   - **Start Command:** `uvicorn web_app:app --host 0.0.0.0 --port $PORT`
4. Clique em **Deploy**

---

## 📌 Versão Atual

**1.1.0** — Integração ViaCEP + Deploy REST

Veja o histórico completo em [CHANGELOG.md](CHANGELOG.md).

---

## 👤 Autor

**Renzo Machado Alves Vaz** — eusourenzo@gmail.com

---

## 🔗 Repositório

https://github.com/renzovaz/Boot-Camp-etapa-inicial-Controle-de-estoque-para-microempreendedores-

---

## 📄 Licença

Este projeto está licenciado sob a [GPL-3.0](LICENSE).
