# Changelog

Todas as mudanças notáveis neste projeto serão documentadas aqui.

O formato segue o padrão [Keep a Changelog](https://keepachangelog.com/pt-BR/1.0.0/)
e este projeto adere ao [Versionamento Semântico](https://semver.org/lang/pt-BR/).

---

## [1.0.0] — 2025-01-01

### Adicionado

- Comando `add` para cadastro e reposição de produtos
- Comando `sell` para registro de vendas com baixa automática de estoque
- Comando `list` para visualização de todos os produtos com status visual
- Comando `alerts` para exibição de produtos abaixo do estoque mínimo
- Comando `report` para relatório de giro de mercadorias com valor financeiro
- Comando `remove` para remoção de produtos do inventário
- Persistência de dados em JSON local (`~/.stockguard/inventory.json`)
- Suporte a arquivo de dados customizado via flag `--data`
- Testes automatizados com pytest cobrindo 20+ cenários
- Linting e análise estática com Ruff
- Pipeline de CI com GitHub Actions (Python 3.10, 3.11, 3.12)
- Versionamento semântico via `pyproject.toml`
- Documentação completa em `README.md`