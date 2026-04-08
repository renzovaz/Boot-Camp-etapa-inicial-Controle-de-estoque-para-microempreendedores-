# StockGuard 🛡️
 
> Controle de estoque para microempreendedores — automatiza baixas em tempo real, dispara alertas de estoque mínimo e gera métricas de giro de mercadorias.
    
## O Problema
 
Microempreendedores — donos de papelarias, mercearias, bazares, depósitos — perdem dinheiro todo dia por falta de controle de estoque. Sem saber o que acabou, quando repor ou o que mais vende, decisões erradas viram prejuízo: falta de produto na hora da venda, compras desnecessárias que imobilizam caixa, e perdas por vencimento ou obsolescência.
 
## A Solução
 
O **StockGuard** é uma ferramenta CLI leve, que roda diretamente no terminal, sem precisar de internet nem de servidor. Ela permite:
 
- Cadastrar e repor produtos no estoque
- Registrar vendas (baixas automáticas)
- Receber alertas quando o estoque cai abaixo do mínimo definido
- Visualizar relatório de giro de mercadorias com valor financeiro
- Remover produtos do inventário
 
Os dados ficam salvos localmente em `~/.stockguard/inventory.json`, sem necessidade de banco de dados externo.
 
## Público-alvo
 
Microempreendedores individuais (MEI) e pequenos negócios que precisam de controle simples, rápido e confiável de inventário.
 
---
 
## Funcionalidades principais
 
| Comando | O que faz |
|---------|-----------|
| `stockguard add NOME QTD` | Cadastra ou repõe produto |
| `stockguard sell NOME QTD` | Registra venda (baixa automática) |
| `stockguard list` | Lista todos os produtos com status |
| `stockguard alerts` | Exibe produtos abaixo do estoque mínimo |
| `stockguard report` | Relatório de giro com valor financeiro |
| `stockguard remove NOME` | Remove produto do inventário |
 
---
 
## Tecnologias utilizadas
 
- **Python 3.10+** — sem dependências externas em produção
- **pytest** — testes automatizados
- **Ruff** — linting e análise estática
- **GitHub Actions** — integração contínua (CI)
- **pyproject.toml** — manifesto e configuração centralizada
 
---
 
## Instalação
 
### Pré-requisitos
 
- Python 3.10 ou superior
- pip
 
### Instalar a partir do repositório
 
```bash
# Clone o repositório
git clone https://github.com/SEU_USUARIO/stockguard.git
cd stockguard
 
# Instale em modo editável (desenvolvimento)
pip install -e ".[dev]"
```
 
### Verificar a instalação
 
```bash
stockguard --help
```
 
---
 
## Como usar
 
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
 
```
Relatório de giro de mercadorias
──────────────────────────────────────────────────────────────────────
Produto                      Vendidos   Val. vendido  Estoque atual
──────────────────────────────────────────────────────────────────────
Caneta Azul                        20      R$ 30.00     R$ 120.00
Caderno A4                          0       R$ 0.00     R$ 240.00
Borracha                            0       R$ 0.00       R$ 6.40  ⚠
```
 
### Arquivo de dados alternativo
 
```bash
stockguard --data /caminho/customizado.json list
```
 
---
 
## Testes
 
```bash
# Executar todos os testes
pytest
 
# Com cobertura de código
pytest --cov=stockguard --cov-report=term-missing
```
 
Os testes cobrem:
- Caminho feliz (operações corretas)
- Entradas inválidas (quantidade negativa, nome vazio, preço negativo)
- Casos limite (vender exatamente o estoque disponível, quantidade zero)
- Alertas e relatórios
- Serialização/desserialização de dados
 
---
 
## Linting
 
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
 
## CI com GitHub Actions
 
A pipeline executa automaticamente em todo `push` e `pull_request`:
 
1. Instala dependências
2. Executa `ruff check` (lint)
3. Executa `ruff format --check` (formatação)
4. Executa `pytest` com cobertura
 
Compatível com Python 3.10, 3.11 e 3.12.
 
---
 
## Estrutura do projeto
 
```
stockguard/
├── src/
│   └── stockguard/
│       ├── __init__.py      # versão do pacote
│       ├── cli.py           # interface de linha de comando
│       ├── inventory.py     # lógica de negócio
│       └── storage.py       # persistência em JSON
├── tests/
│   ├── __init__.py
│   └── test_inventory.py    # testes automatizados
├── .github/
│   └── workflows/
│       └── ci.yml           # pipeline de CI
├── pyproject.toml           # manifesto, versão e configurações
├── CHANGELOG.md
├── LICENSE
└── README.md
```
 
---
 
## Versão atual
 
**1.0.0** — veja o [CHANGELOG](CHANGELOG.md) para histórico de mudanças.
 
---
 
## Autor
 
Seu Nome Aqui — [seuemail@exemplo.com](mailto:seuemail@exemplo.com)
 
Repositório: [https://github.com/SEU_USUARIO/stockguard](https://github.com/SEU_USUARIO/stockguard)
 
---
 
## Licença
 
Este projeto está licenciado sob a [MIT License](LICENSE).