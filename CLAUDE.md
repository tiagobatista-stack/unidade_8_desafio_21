# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Comece por **`docs/SPEC_SDD.md`** (especificação SDD: princípios invariantes, requisitos, verificação, decisões, backlog e prompt de retomada); o texto normativo completo das regras está no `HANDOFF_CLAUDE_CODE.md`.

## Estado atual do repositório

"Inspeções Simuladas" (laboratório SEMA/MT, **dados 100% fictícios**). Backend (`backend/`), frontend (`frontend/`) e E2E (`e2e/`) estão implementados; faltam a documentação M0 (`docs/requisitos.md`, ADRs etc.) e a matriz CA01–CA110 da S4. O status das sprints está na seção 10 do handoff; evidências em `docs/evidencias/`.

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
- Numeração CA01–CA73 é estável; não renumerar. A rodada R1 (23/10/2026) acrescentou RN35–RN38 e CA74–CA85 (seção 16 do handoff).
- `numero_processo` é obrigatório na API (texto livre ≤60, editável em Aberta/Em andamento) mas **nulo no banco** para linhas antigas; `database._garantir_colunas` acrescenta a coluna a bancos criados antes dela (sem Alembic).
- `GET /inspecoes` aceita `status` repetido (grupos do Painel) e `numero_processo`; o detalhe traz `campos_editaveis` (a regra RN14 fica no backend, a tela só renderiza).
- Locais: a tela Locais lista, cria e edita (RN36, RN40); inativar/excluir fica fora. `numero_car` é texto livre (nunca rejeitar formato sem confirmar com o usuário) e os proprietários vivem em tabela própria, com telefone só em dígitos.
- Ao fechar, `inspecao_service.fechar` grava a cópia do empreendimento (`empreendimento_json`) e reserva o `numero_relatorio` (`numeracao_service`, contador por ano) **antes** de mudar resultado/status (autoflush + CHECKs); a finalizada exibe a cópia, as demais os dados atuais do Local.
- Relatório: `GET /inspecoes/{id}/relatorio` devolve só o **corpo a partir do item 5** (cabeçalho mínimo, 5.1–5.3, 6 e 7, a conclusão é opcional por `?incluir_conclusao=false`; o backend monta tudo, inclusive a regra do resultado) e `pages/RelatorioPage.tsx`. A **capa** (itens 1 a 4) e a assinatura são do sistema da SEMA: este sistema só organiza os dados para copiar (`GET /inspecoes/{id}/dados-capa`, `services/capa_service.py`, `pages/CapaPage.tsx`). A impressão usa `@media print` e uma regra `@page` injetada pela página (rodapé e marca de prévia em caixas de margem); `position: fixed` NÃO serve para rodapé (cobriu conteúdo no PDF). Nada de biblioteca de PDF no backend sem consultar o usuário.
- **R4 (capa da SEMA):** a equipe técnica (>=1 membro) é obrigatória para fechar (422 `FECHAMENTO_BLOQUEADO`, detalhe `equipe`); depois do fechamento só `numero_relatorio_sema` e o número de cada ato (por `id`) são editáveis (RN50), o resto continua 409 `INSPECAO_IMUTAVEL`. `equipe` e `atos` são substituídas por inteiro no PATCH. O protocolo é o `numero_processo`; o número `NNNN/AAAA` é a **Ref. interna**. CPF/CNPJ validam dígitos e ficam só com dígitos no banco; CEP tem 8 dígitos. Coordenadas aceitam decimal ou GMS (`latitude_gms`/`longitude_gms`), convertidas no serviço (`domain/coordenadas.py`, nunca 60" ao arredondar). Erros de validação do Pydantic saem em português com rótulo (`errors._mensagem_pt`). As listas de assunto e de tipos de ato existem no backend (`domain/constantes.py`) e no front (`src/constantes.ts`): mudar nos dois.
- Windows/PowerShell: ao criar arquivos com Python use `encoding="utf-8"` (ou `PYTHONUTF8=1`); o padrão cp1252 já truncou arquivo e gravou bytes inválidos.
- Migração sem Alembic: `database._garantir_colunas` (ADD COLUMN e índices) + `services/migracao_dados.preencher_legado` (cópia e numeração das finalizadas antigas), ambos idempotentes e chamados na subida da API.
- Dados 100% fictícios no seed, testes e capturas (LGPD): proprietários "… Fictício", telefones `(65) 90000-000N`, CAR `MT-5107925-0000…`.
- Parte B decidida: vistoria antes do agendamento **fica bloqueada** (aviso preventivo, não relaxar o CHECK de datas); `respondido_em` por item **adiado** (não implementar sem pedido); exportação dos itens **feita** em `export_itens_service` (CSV separado, `/exportacao/itens.csv`, sem alterar `/exportacao/inspecoes.csv`).
- Formulários: todo input/select/textarea com `id`, `name` e `label htmlFor`; há teste genérico (`correcoes-a.test.tsx`) que quebra se faltar algum.
- Frontend publicado na Vercel com backend local: `VITE_API_URL` (build) e `CORS_ORIGINS` (backend); detalhes no README.
- Seed de testes é fixture (S1A); o endpoint `POST /utilitarios/carregar-exemplos` só existe na S3 (409 `BANCO_JA_POVOADO` se já houver dados).

## Comandos (executados neste repositório)

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

# e2e/ (sobe API na 8100 e Vite na 5180 com banco temporário; salva telas em docs/evidencias/telas)
npx playwright test
```

`INSPECOES_HOJE=AAAA-MM-DD` fixa a data "de hoje" da API (o relógio nos testes unitários é fixado por código). O modelo de checklist (6 itens) é criado na inicialização; os exemplos só entram por `POST /utilitarios/carregar-exemplos`.

`.gitignore` obrigatório: `*.db`, `backend/data/`, `.env`, `venv/`, `.venv/`, `node_modules/`, `dist/`, `__pycache__/`. Mapa de pastas alvo na seção 14 do handoff.
