# Inspeções Simuladas

Ferramenta **local, para um único usuário**, que simula o fluxo de inspeções de um laboratório da SEMA/MT: cadastrar uma inspeção com data de agendamento, registrar os itens do checklist, anotar o contexto e as fotografias da vistoria e fechar a inspeção com resultado calculado.

> **Aviso: todos os dados são fictícios.** Nenhum dado real da SEMA/MT é usado. As imagens de exemplo são geradas por programa.

> **Status:** MVP implementado e testado (backend, frontend e E2E). Frontend publicado na Vercel; o backend roda localmente. Evidências e telas em [`docs/evidencias/`](docs/evidencias/). Pendências e limitações no fim deste arquivo.

**Site publicado (frontend):** https://unidade-8-desafio-21.vercel.app. Ele só mostra dados quando o backend está rodando no mesmo computador do navegador (veja [Frontend na Vercel](#frontend-na-vercel-com-backend-local)).

## Funcionalidades

- Cadastro de inspeção (**número do processo**, local, data de agendamento, objetivo, observações), com código sequencial `INS-NNN` e checklist de 6 itens copiado do modelo (3 críticos). O número do processo é obrigatório e de texto livre (ex.: `SEMA-PRO-2026/12345`).
- **Novo local pela própria tela de nova inspeção** (nome, município, tipo, latitude e longitude dentro de Mato Grosso); o local criado já fica selecionado.
- **Editar inspeção** (botão na lista e no detalhe) apenas nos campos permitidos pelo status: Aberta (processo, local, agendamento, objetivo, observações) e Em andamento (processo, data de realização, observações).
- Registro da situação de cada item (Conforme, Não conforme, Não se aplica), com item avulso opcional. Item não conforme exige observação para fechar.
- Observações da vistoria (até 2000 caracteres) e fotos (JPEG, PNG ou WebP, até 5 MB, no máximo 20 por inspeção), cada uma com **anotação obrigatória**. O tipo é validado pelo conteúdo, o EXIF/GPS é removido e é gerada miniatura de 320 px.
- Fechamento com resultado calculado: **Reprovada** se algum item crítico for não conforme, **Aprovada com ressalvas** se houver outro item não conforme, **Aprovada** nos demais casos. Fechamento bloqueado lista cada item pendente.
- Cancelamento com motivo (somente inspeções Abertas). Inspeções finalizadas ou canceladas ficam somente leitura.
- Painel com três indicadores (**Inspeções**, **Pendências**, **Finalizadas**) **clicáveis**: cada um abre a lista da categoria (Inspeções exclui as canceladas). A lista tem filtros de status e período, **busca por número do processo** e mostra o filtro ativo.
- Carga de dados de exemplo (5 inspeções com números de processo fictícios e 9 fotos) e exportação CSV (inclui `numero_processo`).

Regra importante (decisão P1 do handoff): registrar o primeiro item de uma inspeção agendada para o futuro é **bloqueado** (422) até a data do agendamento ou até reagendar a inspeção.

## Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.12, FastAPI, SQLAlchemy, SQLite, Pillow, pytest |
| Frontend | React 18, Vite, TypeScript, TanStack Query, React Router, Vitest, Testing Library |
| E2E | Playwright (Chromium) |

A API usa o prefixo `/api/v1` e escuta apenas em `127.0.0.1`. Não há login no MVP. As regras de negócio ficam só no backend (`routers → services → repositories`, com `domain` de funções puras).

## Instalação

**Pré-requisitos:** Python 3.12+, Node.js 20+ (testado com Node 22) e Git. Não é preciso banco externo: o SQLite é criado automaticamente.

```
git clone https://github.com/tiagobatista-stack/unidade_8_desafio_21.git
cd unidade_8_desafio_21
```

Backend (em `backend/`):

```
python -m venv .venv
.venv\Scripts\activate        # Linux/macOS: source .venv/bin/activate
pip install -e ".[dev]"
```

Frontend (em `frontend/`):

```
npm install
```

Só para rodar o E2E (em `e2e/`): `npm install` e `npx playwright install chromium`.

## Execução

Em dois terminais, com o backend primeiro.

**1. Backend** (em `backend/`, com o ambiente virtual ativo), escutando só em `127.0.0.1`:

```
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Na primeira execução ele cria `backend/data/inspecoes.db` e o modelo de checklist. Verificação rápida: `http://127.0.0.1:8000/api/v1/health` deve responder `{"status":"ok"}`.

**2. Frontend** (em `frontend/`), porta 5173, com proxy de `/api` para o backend:

```
npm run dev
```

**3. Usar:** abra http://localhost:5173. Num banco novo não há locais: crie um em **Nova inspeção → + Novo local** ou clique em **Carregar exemplos** no Painel para criar 4 locais, 5 inspeções e 9 fotos fictícias (o Painel passa a mostrar 5 / 2 / 3). A carga só é aceita em banco sem dados.

Fluxo típico: **Nova inspeção** (informe o número do processo) → abrir a inspeção → responder o checklist (a inspeção passa a Em andamento) → registrar observações e fotos com anotação → **Fechar inspeção** (o resultado é calculado) ou **Cancelar** (somente Aberta). **Exportar CSV** no Painel baixa todas as inspeções.

Para usar o frontend publicado na Vercel com o seu backend local, veja [Frontend na Vercel](#frontend-na-vercel-com-backend-local).

### Variáveis de ambiente (todas opcionais)

| Variável | Onde | Efeito |
|---|---|---|
| `DATABASE_URL` | backend | Padrão: `sqlite:///backend/data/inspecoes.db` |
| `FOTOS_DIR` | backend | Padrão: `backend/data/fotos` |
| `CORS_ORIGINS` | backend | Origens liberadas, separadas por vírgula. Sem ela, nenhuma origem externa é aceita |
| `INSPECOES_HOJE` | backend | Fixa a data "de hoje" (`AAAA-MM-DD`), usada no E2E |
| `API_URL` | Vite (dev) | Destino do proxy `/api` (padrão `http://127.0.0.1:8000`) |
| `VITE_API_URL` | build do frontend | Endereço da API embutido no build (vazio = mesma origem) |

## Testes

```
pytest -q                     # em backend/  (229 testes)
npm test -- --run             # em frontend/ (59 testes)
npm run build                 # em frontend/ (tsc + vite)
npx playwright test           # em e2e/      (11 passos; sobe API e Vite em portas próprias e regrava as telas)
```

Primeira vez no E2E: `cd e2e && npm install && npx playwright install chromium`. O E2E usa banco SQLite temporário e não toca em `backend/data/`. O CI (`.github/workflows/ci.yml`) roda `pytest`, `npm test` e `npm run build`; o E2E **não** roda no CI.

Resultados e capturas das telas: [`docs/evidencias/S2-S3-E2E.md`](docs/evidencias/S2-S3-E2E.md), [`S1A.md`](docs/evidencias/S1A.md), [`S1B.md`](docs/evidencias/S1B.md) e a pasta [`docs/evidencias/telas/`](docs/evidencias/telas/).

## Estrutura de pastas

```
├── README.md  HANDOFF_CLAUDE_CODE.md  PLANO_EXECUTAVEL.md  CLAUDE.md
├── .github/workflows/ci.yml
├── docs/evidencias/   testes por sprint, telas do Playwright, CSV exportado
├── backend/           app/ (routers, services, repositories, domain, models, schemas, storage, seed), tests/
├── frontend/          src/ (api, pages, components, hooks, utils, tests), vercel.json
└── e2e/               Playwright (fluxo completo + geração de telas)
```

## Frontend na Vercel com backend local

O backend continua na máquina do usuário (`127.0.0.1:8000`); só o frontend estático está na Vercel, e é o **navegador** que chama a API local. Por isso só funciona no computador onde o backend está rodando, e o site publicado não guarda nada.

1. **Backend**, liberando apenas a origem do site (sem barra no final):
   ```
   $env:CORS_ORIGINS="https://unidade-8-desafio-21.vercel.app"      # cmd: set CORS_ORIGINS=...
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Permissão no navegador:** no primeiro acesso, Chrome/Edge pedem permissão para o site acessar a rede local (é o acesso a `127.0.0.1`). É preciso **permitir**; se negar, o painel mostra "Não foi possível conectar à API." e a permissão pode ser refeita nas configurações do site. Firefox também funciona; Safari bloqueia.
3. **Projeto na Vercel** (`unidade-8-desafio-21`, equipe `tiago-alexandre`): *Root Directory* `frontend`, preset Vite, variável `VITE_API_URL=http://127.0.0.1:8000` em Production e Preview (embutida no build; mudá-la exige novo deploy). O `frontend/vercel.json` define o build e redireciona as rotas para `index.html`. O deploy automático por push está desativado.
4. **Novo deploy** pela CLI, a partir da **raiz do repositório** (o Root Directory do projeto já é `frontend`): `npm i -g vercel`, `vercel login`, `vercel link` e `vercel deploy --prod`.

Para testar um build em outra origem sem a Vercel: `VITE_API_URL=http://127.0.0.1:8000 npx vite build` e `npx vite preview --port 4173`, com `CORS_ORIGINS=http://localhost:4173` no backend.

## Dados e backup

O banco fica em `backend/data/inspecoes.db` e as fotos em `backend/data/fotos/`. O backup é manual: copie **o arquivo `.db` e a pasta `fotos/`** juntos. Nada disso é versionado. O utilitário `GET /api/v1/utilitarios/verificar-fotos` lista inconsistências entre registros e arquivos.

## Fora do escopo do MVP

Login e perfis com permissão real, múltiplos usuários, nuvem ou sincronização, app móvel, cadastro de locais e de modelos de checklist, reabertura de inspeção finalizada, histórico e auditoria, relatórios em PDF, mapa e geolocalização, edição de imagens, backup automático e integração com sistemas reais. A lista completa está na seção 13 do handoff.

## Migração futura para PostgreSQL

O esquema usa apenas tipos e constraints portáveis. O caminho é: definir `DATABASE_URL`, adotar Alembic, revisar os CHECKs e rodar a suíte de API em PostgreSQL no CI. Hospedar o backend na nuvem (por exemplo, na própria Vercel) também exigiria trocar as fotos em disco por armazenamento de objetos, porque o sistema de arquivos das funções serverless é efêmero.

## Documentação

- [`HANDOFF_CLAUDE_CODE.md`](HANDOFF_CLAUDE_CODE.md): fonte única do escopo (regras de negócio, endpoints, contrato de erro, critérios de aceite, dados de exemplo e pendências).
- [`PLANO_EXECUTAVEL.md`](PLANO_EXECUTAVEL.md): plano por sprint, com prompts, verificações e critérios de aceite.
- [`CLAUDE.md`](CLAUDE.md): orientações para o Claude Code neste repositório.

## Limitações

- **Uso local e de um único usuário:** sem login, sem perfis com permissão e sem acesso de outros computadores. A API só escuta em `127.0.0.1`.
- **Frontend na Vercel depende do backend local:** só funciona no computador onde o backend roda, exige `CORS_ORIGINS` e a permissão do navegador para acessar a rede local; Safari bloqueia. Em outros dispositivos o site abre, mas sem dados.
- **Armazenamento local:** banco SQLite e fotos em disco, backup manual (`.db` + `fotos/`). Hospedar o backend em nuvem exige PostgreSQL e armazenamento de objetos (ver abaixo).
- **Locais e checklist:** a tela só **cria** locais (não edita nem inativa); o modelo de checklist (6 itens) é fixo e não tem tela de edição.
- **Número do processo:** texto livre, sem validação de formato e não único. Inspeções criadas antes do campo existir ficam com o número vazio ("—") até serem editadas; o banco antigo é atualizado sozinho na inicialização da API (coluna adicionada sem perder dados).
- **Lista:** mostra até 100 inspeções por consulta (sem paginação na tela).
- **Regras do fluxo:** só se fecha inspeção Em andamento; só se cancela inspeção Aberta; inspeção finalizada ou cancelada não pode ser reaberta nem editada; inspeção agendada para o futuro não aceita item respondido (P1).
- **Fotos:** uma por requisição, JPEG/PNG/WebP, até 5 MB e 20 por inspeção; o arquivo original é regravado só com os pixels (sem metadados). Sem edição, rotação ou câmera. O travessão "—" do texto das fotos de exemplo aparece como quadrado (a fonte padrão do Pillow não tem o glifo).
- **Sem relatórios em PDF, mapa, histórico/auditoria, busca textual ou backup automático** (lista completa na seção 13 do handoff).
- **Testes:** o E2E roda só em Chromium e fora do CI; o site publicado foi validado com a permissão de rede local concedida por script, não pelo pedido real do navegador. Não há testes de acessibilidade nem de carga.
- **Persistência após reiniciar a API (CA22):** validada manualmente na S1A; o E2E recarrega a página, mas não reinicia a API.

## Pendências do projeto

- **Documentação M0 não escrita:** `docs/requisitos.md`, `docs/criterios-aceite.md`, as ADRs e `docs/migracao-postgresql.md` não existem; o escopo vale como está no handoff.
- **Matriz CA01–CA85 incompleta:** os critérios cobertos por teste estão nos arquivos de evidência, mas a matriz final (sprint S4) não foi montada.
- **Licença e visibilidade do repositório (P10):** indefinidas.
- As demais pendências (P1–P9) e os padrões adotados estão na seção 9 do handoff; P11 (versões) está resolvida em [Instalação](#instalação).
