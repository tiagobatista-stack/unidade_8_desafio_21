# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Estado atual do repositório

Hoje existem **apenas dois documentos** (sem código, sem Git): `HANDOFF_CLAUDE_CODE.md` e `PLANO_EXECUTAVEL.md`. O projeto, "Inspeções Simuladas" (laboratório SEMA/MT, **dados 100% fictícios**), será construído por sprints (M0 → S0 → S1A → S1B → S2A → S2B → S3 → S4). O status das sprints está na seção 10 do handoff.

- `HANDOFF_CLAUDE_CODE.md` é a **fonte única de verdade** do escopo (entidades, RN01–RN34, endpoints, contrato de erro, CA01–CA73, seed, fora de escopo). O que não está nele está fora do escopo; dúvida de regra → seção 9 (Pendências P1–P11); se não estiver lá, perguntar antes de decidir.
- `PLANO_EXECUTAVEL.md` traz, por sprint, objetivo, prompt, comandos de verificação, critérios de aceite e condição de parada. Os documentos referem `docs/PLANO_EXECUTAVEL.md` na estrutura alvo.

## Regras de trabalho (do handoff, seção 0)

- **Uma sprint por vez**: execute só a pedida, pare ao cumprir os critérios de aceite e relate evidências (`docs/evidencias/<sprint>.md`). Cada sprint termina com testes verdes, commits Conventional Commits e atualização da seção 10 do handoff.
- Regras de negócio **só** na camada de serviço/domínio (backend); o front exibe, valida obrigatoriedade e repassa erros.
- Se uma verificação falhar, corrija a causa; nunca enfraqueça teste nem pule critério.
- Sem login no MVP; API escuta só em `127.0.0.1`. Sem dados/imagens reais (imagens de exemplo geradas por Pillow).
- Documentação e mensagens ao usuário em português; identificadores em português sem acento (ex.: `data_agendamento`).
- Push/criação de repositório no GitHub só com confirmação explícita.

## Arquitetura alvo

- **Backend** (`backend/`): Python 3.12+ / FastAPI / SQLAlchemy / SQLite (`backend/data/inspecoes.db`, `DATABASE_URL` configurável, `PRAGMA foreign_keys=ON`). Camadas `routers → services → repositories`, com `domain/` de funções puras (resultado, transições, datas, coordenadas, texto, imagem). Prefixo `/api/v1`. Tabelas via `create_all` (Alembic só na migração para PostgreSQL; usar apenas tipos/constraints portáveis).
- **Frontend** (`frontend/`): React + Vite + TypeScript, TanStack Query, Vitest + Testing Library; proxy `/api` → `127.0.0.1:8000`. Datas ISO na API, `dd/mm/aaaa` na UI, "—" para vazio.
- **`clock.py` injetável**: "hoje" nos testes é fixo em **2026-10-23**.
- **Erros**: contrato único `{"erro": {"codigo","mensagem","detalhes":[{"campo","mensagem"}]}}` (códigos na seção 6 do handoff), gerado por exceção de negócio + handler em `errors.py`.
- **Fotos (ADR-002)**: metadados no banco, arquivos em disco `backend/data/fotos/{inspecao_id}/original|miniatura/{uuid}.ext` via interface `storage`; tipo validado pelo **conteúdo**; EXIF removido; miniatura com lado maior 320 px; servidas só pela API. Backup = `.db` + `data/fotos/`. Ordem de validação no upload: estado da inspeção (409) → campos/arquivo (422/413/415) → limite/duplicidade (409) → só então gravar (arquivo antes do registro, compensar em falha).
- Sem DELETE de inspeção (cancelamento com motivo). FINALIZADA e CANCELADA são imutáveis (inclui itens e fotos).

## Pontos fáceis de errar

- Cinco campos de texto distintos: `observacoes` (cadastro), `observacoes_vistoria` (narrativa, ≤2000), `observacao` (item; obrigatória se NÃO CONFORME), `legenda` (foto, ≤200), `anotacao` (foto, obrigatória, 1..1000 após trim).
- Resultado no fechamento: NC crítico → REPROVADA; senão qualquer NC → APROVADA_COM_RESSALVAS; senão APROVADA. Só fecha se EM_ANDAMENTO e todos os itens respondidos.
- **P1**: o 1º item registrado em inspeção agendada para o futuro **não** preenche realização; retorna 422 `DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO`.
- Indicadores: Inspeções (≠ CANCELADA), Pendências (ABERTA+EM_ANDAMENTO), Finalizadas; invariante Pend + Final = Inspeções; seed esperado **5 / 2 / 3**, numa única consulta agregada.
- Numeração CA01–CA73 é estável; não renumerar.
- Seed de testes é fixture (S1A); o endpoint `POST /utilitarios/carregar-exemplos` só existe na S3 (409 `BANCO_JA_POVOADO` se já houver dados).

## Comandos (alvo; confirmar na S0 e fechar na S4)

```
# backend/ (venv: python -m venv .venv; Windows: .venv\Scripts\activate)
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000
pytest -q                                   # tudo
pytest -q tests/unit | tests/service | tests/api
pytest -q -k foto                           # filtro por nome
pytest -q tests/api/test_health.py::nome    # um teste

# frontend/
npm install && npm run dev                  # porta 5173
npm test -- --run && npm run build
```

`.gitignore` obrigatório: `*.db`, `backend/data/`, `.env`, `venv/`, `.venv/`, `node_modules/`, `dist/`, `__pycache__/`. Mapa de pastas alvo na seção 14 do handoff.
