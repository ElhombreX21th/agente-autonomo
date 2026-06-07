# Agente Autônomo

Projeto de estudo para estruturar um assistente local com planejamento, memória e fluxo de tarefas.

Status: repositório em fase inicial. A documentação abaixo define a proposta do projeto e a direção técnica recomendada para evolução.

## Screenshots

### Console Preview

![Agent console preview](docs/screenshots/agent-console-preview.svg)

### Workflow Overview

![Agent workflow overview](docs/screenshots/agent-workflow-overview.svg)

## Objetivo

Criar uma base organizada para um assistente capaz de receber uma tarefa, dividir em etapas, consultar memória/contexto e retornar uma resposta clara ao usuário.

## Conceitos Demonstrados

- Planejamento de tarefas
- Memória local de contexto
- Organização modular
- Fluxo de decisão controlado
- Documentação técnica para evolução
- Preparação para testes automatizados

## Stack Sugerida

- Python 3.10+
- FastAPI ou CLI Python
- JSON ou SQLite para memória local
- pytest para testes automatizados
- GitHub Actions para validação contínua

## Estrutura Recomendada

```text
agente-autonomo/
├── app/
│   ├── agent.py
│   ├── planner.py
│   ├── memory.py
│   ├── tools.py
│   └── cli.py
├── tests/
│   └── test_agent.py
├── docs/
│   └── screenshots/
└── README.md
```

## Roadmap

- [ ] Criar estrutura base do projeto
- [ ] Implementar CLI inicial
- [ ] Criar módulo de planejamento
- [ ] Criar memória local simples
- [ ] Adicionar testes automatizados
- [ ] Criar API com FastAPI
- [ ] Adicionar logs e validações
- [ ] Preparar versão demonstrável para portfolio

## Como Rodar Futuramente

Quando o código-base estiver implementado, a execução local deverá seguir um fluxo parecido com:

```bash
python -m app.cli
```

E os testes:

```bash
pytest
```

## Valor para Portfolio

Este projeto pode mostrar domínio de arquitetura de assistentes de IA, organização de software, separação de responsabilidades, testes e documentação. Para ficar forte em entrevistas, o próximo passo é implementar um MVP funcional pequeno, mas completo.

## Autor

Criado por ElhombreX21th.
