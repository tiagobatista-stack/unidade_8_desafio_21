# Inspeções Simuladas

Ferramenta **local, para um único usuário**, que simula o fluxo de inspeções de um laboratório da SEMA/MT: cadastrar uma inspeção com data de agendamento, registrar os itens do checklist, anotar o contexto e as fotografias da vistoria e fechar a inspeção com resultado calculado.

> **Aviso: todos os dados são fictícios.** Nenhum dado real da SEMA/MT é usado. As imagens de exemplo são geradas por programa.

> **Status:** MVP implementado e testado localmente (backend, frontend e E2E). Resultados e telas em `docs/evidencias/`. Pendências abertas (licença, publicação) no fim deste arquivo.

## Funcionalidades

- Cadastro de inspeção (local, data de agendamento, objetivo, observações), com código sequencial `INS-NNN` e checklist de 6 itens copiado do modelo.
- Registro da situação de cada item (Conforme, Não conforme, Não se aplica), com item avulso opcional.
- Observações da vistoria (texto de até 2000 caracteres) e fotos (JPEG, PNG ou WebP, até 5 MB, no máximo 20 por inspeção), cada uma com anotação obrigatória.
- Fechamento com resultado calculado: **Reprovada** se algum item crítico for não conforme, **Aprovada com ressalvas** se houver outro item não conforme, **Aprovada** nos demais casos.
- Cancelamento com motivo (somente inspeções Abertas). Inspeções finalizadas ou canceladas ficam somente leitura.
- Painel com três indicadores (**Inspeções**, **Pendências**, **Finalizadas**), carga de dados de exemplo e exportação CSV.

## Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python, FastAPI, SQLAlchemy, SQLite, Pillow, pytest |
| Frontend | React, Vite, TypeScript, TanStack Query, Vitest, Testing Library |

A API usa o prefixo `/api/v1` e escuta apenas em `127.0.0.1`. Não há login no MVP.

## Como rodar

> Versões usadas: Python 3.12 e Node 22 (CI usa Node 20). Comandos abaixo foram executados neste repositório.

Backend (em `backend/`):

```
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Frontend (em `frontend/`, porta 5173, com proxy de `/api` para o backend):

```
npm install
npm run dev
```

Abra http://localhost:5173 e use **Carregar exemplos** no Painel para popular dados fictícios (locais, 5 inspeções, 9 fotos geradas por programa).

Testes:

```
pytest -q                     # em backend/ (199 testes)
npm test -- --run             # em frontend/ (36 testes)
npm run build                 # em frontend/
npx playwright test           # em e2e/ (sobe API e Vite em portas próprias e salva telas em docs/evidencias/telas)
```

Primeira vez no E2E: `cd e2e && npm install && npx playwright install chromium`. A variável `INSPECOES_HOJE=AAAA-MM-DD` fixa a data "de hoje" da API (usada no E2E).

## Estrutura de pastas (alvo)

```
├── README.md  HANDOFF_CLAUDE_CODE.md  CLAUDE.md  .gitignore
├── .github/workflows/ci.yml
├── docs/        evidências (testes, telas do Playwright, CSV exportado)
├── backend/     app/ (routers, services, repositories, domain, models, schemas, storage, seed), tests/
├── frontend/    src/ (api, pages, components, hooks, utils, tests)
└── e2e/         Playwright (fluxo completo + geração de telas)
```

## Dados e backup

O banco fica em `backend/data/inspecoes.db` e as fotos em `backend/data/fotos/`. O backup é manual: copie **o arquivo `.db` e a pasta `fotos/`** juntos. Nada disso é versionado.

## Fora do escopo do MVP

Login e perfis com permissão real, múltiplos usuários, nuvem ou sincronização, app móvel, cadastro de locais e de modelos de checklist, reabertura de inspeção finalizada, histórico e auditoria, relatórios em PDF, mapa e geolocalização, edição de imagens, backup automático e integração com sistemas reais. A lista completa está na seção 13 do handoff.

## Migração futura para PostgreSQL

O esquema usa apenas tipos e constraints portáveis. O caminho é: definir `DATABASE_URL`, adotar Alembic, revisar os CHECKs e rodar a suíte de API em PostgreSQL no CI. Os documentos de requisitos, ADRs e `docs/migracao-postgresql.md` (sprint M0) **ainda não foram escritos**; o escopo vale como está no handoff.

## Documentação

- `HANDOFF_CLAUDE_CODE.md`: fonte única do escopo (regras de negócio, endpoints, contrato de erro, critérios de aceite, dados de exemplo e pendências).
- `PLANO_EXECUTAVEL.md`: plano por sprint, com prompts, verificações e critérios de aceite.

## Pendências abertas

Licença e visibilidade do repositório no GitHub (P10) e versões exatas de Python e Node (P11). As demais pendências e os padrões adotados até decisão estão na seção 9 do handoff.
