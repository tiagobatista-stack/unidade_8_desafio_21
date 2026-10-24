# Inspeções Simuladas

Ferramenta **local, para um único usuário**, que simula o fluxo de inspeções de um laboratório da SEMA/MT: cadastrar uma inspeção com data de agendamento, registrar os itens do checklist, anotar o contexto e as fotografias da vistoria e fechar a inspeção com resultado calculado.

> **Aviso: todos os dados são fictícios.** Nenhum dado real da SEMA/MT é usado. As imagens de exemplo são geradas por programa.

> **Status:** MVP implementado e testado (backend, frontend e E2E). Frontend publicado na Vercel; o backend roda localmente. Evidências, telas e PDFs do relatório em [`docs/evidencias/`](docs/evidencias/). Resumo da última rodada em [O que mudou na rodada R4](#o-que-mudou-na-rodada-r4). Pendências e limitações no fim deste arquivo.

**Site publicado (frontend):** https://unidade-8-desafio-21.vercel.app. Ele só mostra dados quando o backend está rodando no mesmo computador do navegador (veja [Frontend na Vercel](#frontend-na-vercel-com-backend-local)).

## Funcionalidades

- Cadastro de inspeção (**número do processo**, local, data de agendamento, objetivo, observações), com código sequencial `INS-NNN` e checklist de 6 itens copiado do modelo (3 críticos). O número do processo é obrigatório e de texto livre (ex.: `SEMA-PRO-2026/12345`).
- **Locais** (tela própria: listar, cadastrar e editar) com nome, município, tipo, coordenadas dentro de Mato Grosso, **número do CAR** (opcional, texto livre em maiúsculas) e **proprietários** (nome e telefone, em lista com adicionar/remover). Também dá para criar um local na própria tela de nova inspeção; ele já fica selecionado.
- Detalhe da inspeção com o cartão **Empreendimento** (local, CAR e proprietários) e avisos que orientam o que fazer: a inspeção só passa para Em andamento quando se registra a situação de um item; agendamento futuro bloqueia o registro até reagendar; fechar uma inspeção Aberta fica desabilitado com o motivo.
- **Editar inspeção** (botão na lista e no detalhe) apenas nos campos permitidos pelo status: Aberta (processo, local, agendamento, objetivo, observações) e Em andamento (processo, data de realização, observações).
- Registro da situação de cada item (Conforme, Não conforme, Não se aplica), com item avulso opcional. Item não conforme exige observação para fechar.
- Observações da vistoria (até 2000 caracteres) e fotos (JPEG, PNG ou WebP, até 5 MB, no máximo 20 por inspeção), cada uma com **anotação obrigatória**. O tipo é validado pelo conteúdo, o EXIF/GPS é removido e é gerada miniatura de 320 px.
- Fechamento com resultado calculado: **Reprovada** se algum item crítico for não conforme, **Aprovada com ressalvas** se houver outro item não conforme, **Aprovada** nos demais casos. Fechamento bloqueado lista cada item pendente. Ao fechar, o sistema grava uma **cópia dos dados do empreendimento**, então editar o local depois não muda a inspeção finalizada.
- **Dados para a capa e lavratura** (R4): os dados do interessado, assunto, empreendimento, responsáveis, equipe e atos, na ordem da capa do sistema da SEMA, com botões **Copiar** por campo, por bloco e **Copiar tudo**. Este sistema **não gera a capa**.
- **Corpo do relatório** (R4), a partir do item 5 (constatações, providências e conclusão), para anexar depois da capa, imprimível com "Imprimir / Salvar PDF" (veja [Relatório de vistoria](#relatório-de-vistoria)). Inspeção não finalizada gera uma **prévia** sem Ref. interna, marcada "PRÉVIA, NÃO FINALIZADO".
- Cancelamento com motivo (somente inspeções Abertas). Inspeções finalizadas ou canceladas ficam somente leitura.
- Painel com três indicadores (**Inspeções**, **Pendências**, **Finalizadas**) **clicáveis**: cada um abre a lista da categoria (Inspeções exclui as canceladas). A lista tem filtros de status e período, **busca por número do processo** e mostra o filtro ativo.
- Carga de dados de exemplo (4 locais com CAR e proprietários fictícios, 5 inspeções com números de processo fictícios e 9 fotos).
- **Duas exportações CSV** no Painel: **Exportar CSV** (uma linha por inspeção, inclui `numero_processo`) e **Exportar itens (CSV)** (arquivo separado, uma linha por item do checklist, com situação, observação, criticidade e quantidade de fotos de cada item).

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

Fluxo típico: **Locais** (cadastre o empreendimento, com CAR e proprietários) → **Nova inspeção** (informe o número do processo) → abrir a inspeção → responder o checklist (a inspeção passa a Em andamento) → registrar observações e fotos com anotação → **Fechar inspeção** (exige ao menos 1 membro na equipe; o resultado é calculado e o relatório recebe a Ref. interna) ou **Cancelar** (somente Aberta) → **Dados para capa e lavratura** (copiar para o sistema da SEMA) → **Registrar números da SEMA** (número dos atos e do relatório, depois de lavrados lá) → **Gerar relatório**. No Painel, **Exportar CSV** baixa uma linha por inspeção e **Exportar itens (CSV)** baixa uma linha por item do checklist.

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
pytest -q                     # em backend/  (457 testes)
npm test -- --run             # em frontend/ (159 testes)
npm run build                 # em frontend/ (tsc + vite)
npx playwright test           # em e2e/      (16 passos; sobe API e Vite em portas próprias, regrava as telas e gera os PDFs de exemplo do relatório)
```

Primeira vez no E2E: `cd e2e && npm install && npx playwright install chromium`. O E2E usa banco SQLite temporário e não toca em `backend/data/`. O CI (`.github/workflows/ci.yml`) roda `pytest`, `npm test` e `npm run build`; o E2E **não** roda no CI.

Resultados e capturas das telas: [`S1A.md`](docs/evidencias/S1A.md), [`S1B.md`](docs/evidencias/S1B.md), [`S2-S3-E2E.md`](docs/evidencias/S2-S3-E2E.md), [`R1-melhorias.md`](docs/evidencias/R1-melhorias.md), [`R2-melhorias.md`](docs/evidencias/R2-melhorias.md), [`R3-exportacao-itens.md`](docs/evidencias/R3-exportacao-itens.md), [`R4-capa-sema-corpo-relatorio.md`](docs/evidencias/R4-capa-sema-corpo-relatorio.md) (e as de cada sprint, `R4-S1` a `R4-S3`), a pasta [`docs/evidencias/telas/`](docs/evidencias/telas/) e os PDFs do corpo do relatório ([finalizado](docs/evidencias/relatorio-INS-004.pdf), [fluxo completo no padrão do modelo](docs/evidencias/relatorio-corpo-R4.pdf) e [prévia](docs/evidencias/relatorio-previa-INS-005.pdf)).

## Estrutura de pastas

```
├── README.md  HANDOFF_CLAUDE_CODE.md  PLANO_EXECUTAVEL.md  CLAUDE.md
├── .github/workflows/ci.yml
├── docs/evidencias/   testes por rodada, telas do Playwright, PDFs do relatório, CSV exportado
├── backend/           app/ (routers, services, repositories, domain, models, schemas, storage, seed), tests/
├── frontend/          src/ (api, pages, components, hooks, utils, tests), vercel.json
└── e2e/               Playwright (fluxo completo + geração de telas)
```

## Relatório de vistoria

O sistema da SEMA gera a **capa** do relatório técnico (1 Interessado, 2 Assunto, 3 Caracterização do empreendimento e 4 Equipe técnica) e a lavratura dos autos. Este sistema **não gera a capa**: a página **Dados para capa e lavratura** (`/inspecoes/:id/capa`) organiza esses dados para copiar, e o relatório (`/inspecoes/:id/relatorio`, botão **Gerar relatório**) é só o **corpo**, a partir do item 5, para anexar depois da capa.

**Corpo do relatório** (`/inspecoes/:id/relatorio`):
- **Cabeçalho mínimo**, sem título de capa: `Protocolo nº ... | Inspeção INS-xxx | Ref. interna NNNN/AAAA` (e `| Relatório SEMA nº ...` quando informado).
- **5 – Constatações:** 5.1 Relato da vistoria (data e observações da vistoria), 5.2 Checklist (numerado, com totais e itens críticos não conformes destacados) e 5.3 Registro fotográfico (Foto 1, 2…, com legenda, anotação, item vinculado e data de captura; no máximo 2 por página).
- **6 – Providências tomadas:** o texto e os atos lavrados; ato sem número aparece como "nº a definir".
- **7 – Conclusão** (resultado e a regra aplicada): a opção **Incluir conclusão** vem ligada; desligada, o item 7 some (`?incluir_conclusao=false`).
- Ficam **de fora** o empreendimento, a equipe e o interessado (vão na capa) e a assinatura (a autenticação é do sistema da SEMA).

**Ref. interna:** o número interno `NNNN/AAAA`, sequencial por ano, atribuído no fechamento, único e nunca reutilizado. Cancelar ou tentar fechar sem sucesso não consome número. O número oficial que a SEMA atribuir é registrado à parte (**Nº do relatório na SEMA**), mesmo depois do fechamento.

- **Prévia:** inspeção que não está finalizada gera o corpo sem Ref. interna e com a marca "PRÉVIA, NÃO FINALIZADO" (no topo de todas as páginas impressas e na diagonal da primeira).
- **Imprimir / Salvar PDF:** usa a impressão do navegador (papel A4, escolha "Salvar como PDF"). O botão só habilita depois que as imagens carregam. Rodapé com a Ref. interna, INS e "Sistema fictício/simulado" e "Página X de Y" em todas as páginas. Não há biblioteca de PDF no backend.
- **Exemplos:** [`relatorio-INS-004.pdf`](docs/evidencias/relatorio-INS-004.pdf), [`relatorio-corpo-R4.pdf`](docs/evidencias/relatorio-corpo-R4.pdf) (fluxo completo no padrão do modelo: interessado MP, responsável com CPF e endereço de correspondência, 3 membros na equipe, 1 notificação) e [`relatorio-previa-INS-005.pdf`](docs/evidencias/relatorio-previa-INS-005.pdf), gerados pelo E2E com dados fictícios.

## Dados para a capa e a lavratura

Página `/inspecoes/:id/capa` (botão **Dados para capa e lavratura** no detalhe). Blocos na ordem da capa e mais **Atos a lavrar**, cada um com **Copiar** por campo, **Copiar bloco** e **Copiar tudo** (texto simples no formato do modelo). Campo vazio aparece como "Não informado" e destacado, com a contagem no topo; Comarca é opcional. Interessado vazio vira "Demanda interna / de ofício". O texto é montado pelo backend (`GET /api/v1/inspecoes/{id}/dados-capa`). Para preencher o que falta: **Editar inspeção** (interessado, assunto, equipe, providências, atos) e **Locais** (nome fantasia, endereço, coordenadas, responsáveis com CPF/CNPJ e correspondência).

## Dados pessoais (LGPD)

Nome e telefone de proprietários são dados pessoais quando reais. **Este repositório só contém dados inventados**: proprietários "... Fictício", telefones `(65) 90000-000N` e CAR `MT-5107925-0000...`, no seed, nos testes e nas capturas de tela. Dados que você cadastrar ficam no seu computador (`backend/data/`), fora do Git, e o site da Vercel não guarda nada. Não use dados reais de terceiros em demonstrações, capturas ou no repositório.

## Atualizando um banco existente (migração)

Não há Alembic: ao subir a API, `database.criar_tabelas()` e `preencher_legado()` atualizam sozinhos um banco criado por versão anterior, de forma **idempotente** e sem perder dados:

- acrescentam `inspecao.numero_processo`, `inspecao.empreendimento_json`, `inspecao.numero_relatorio` (com índice único) e `local.numero_car`;
- criam as tabelas `proprietario` e `contador_relatorio`;
- (R4) acrescentam, também sem perder dados, as colunas `inspecao.interessado_*`, `assunto_tipo`, `assunto_outro`, `providencias_texto` e `numero_relatorio_sema`; `local.logradouro`, `uf` e `cep`; `proprietario.cpf_cnpj` e `corr_*`; e criam as tabelas `equipe_membro` e `ato_lavrado`. Inspeções e locais antigos ficam com esses campos vazios, e as duas saídas (dados para a capa e corpo do relatório) abrem normalmente, com "Não informado" onde falta dado. **Inspeções antigas ainda não finalizadas precisam de ao menos 1 membro na equipe para fechar**;
- preenchem as inspeções já finalizadas: cópia dos dados do **local atual** (não os do dia do fechamento, que não foram guardados) e número de relatório na ordem do fechamento, no ano de cada fechamento.

Passos: **1)** pare a API; **2)** faça backup de `backend/data/` (o `.db` e a pasta `fotos/`); **3)** atualize o código e suba a API normalmente. Inspeções antigas ficam com o número do processo vazio ("—") até serem editadas. Para começar do zero, pare a API e apague `backend/data/` (isso **apaga todos os dados**).

## Frontend na Vercel com backend local

O backend continua na máquina do usuário (`127.0.0.1:8000`); só o frontend estático está na Vercel, e é o **navegador** que chama a API local. Por isso só funciona no computador onde o backend está rodando, e o site publicado não guarda nada.

1. **Backend**, liberando apenas a origem do site (sem barra no final):
   ```
   $env:CORS_ORIGINS="https://unidade-8-desafio-21.vercel.app"      # cmd: set CORS_ORIGINS=...
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. **Permissão no navegador:** no primeiro acesso, Chrome/Edge pedem permissão para o site acessar a rede local (é o acesso a `127.0.0.1`). É preciso **permitir**; se negar, o painel mostra "Não foi possível conectar à API." e a permissão pode ser refeita nas configurações do site. Firefox também funciona; Safari bloqueia.
3. **Projeto na Vercel** (`unidade-8-desafio-21`, equipe `tiago-alexandre`): *Root Directory* `frontend`, preset Vite, variável `VITE_API_URL=http://127.0.0.1:8000` em Production e Preview (embutida no build; mudá-la exige novo deploy). O `frontend/vercel.json` define o build e redireciona as rotas para `index.html`. **Cada push em `main` gera um deploy de produção** pela integração com o GitHub (conferido pelo histórico de deploys do projeto, `fonte = git`), mesmo com `createDeployments` aparecendo como `disabled` na API da Vercel.
4. **Novo deploy** pela CLI, a partir da **raiz do repositório** (o Root Directory do projeto já é `frontend`): `npm i -g vercel`, `vercel login`, `vercel link` e `vercel deploy --prod`.

Para testar um build em outra origem sem a Vercel: `VITE_API_URL=http://127.0.0.1:8000 npx vite build` e `npx vite preview --port 4173`, com `CORS_ORIGINS=http://localhost:4173` no backend.

## Dados e backup

O banco fica em `backend/data/inspecoes.db` e as fotos em `backend/data/fotos/`. O backup é manual: copie **o arquivo `.db` e a pasta `fotos/`** juntos. Nada disso é versionado. O utilitário `GET /api/v1/utilitarios/verificar-fotos` lista inconsistências entre registros e arquivos.

## Fora do escopo do MVP

Login e perfis com permissão real, múltiplos usuários, nuvem ou sincronização, app móvel, edição de modelos de checklist, inativação e exclusão de locais, reabertura de inspeção finalizada, histórico e auditoria, geração de PDF no servidor, mapa e geolocalização, edição de imagens, backup automático e integração com sistemas reais. A lista completa está na seção 13 do handoff.

## Migração futura para PostgreSQL

O esquema usa apenas tipos e constraints portáveis. O caminho é: definir `DATABASE_URL`, adotar Alembic, revisar os CHECKs e rodar a suíte de API em PostgreSQL no CI. Hospedar o backend na nuvem (por exemplo, na própria Vercel) também exigiria trocar as fotos em disco por armazenamento de objetos, porque o sistema de arquivos das funções serverless é efêmero.

## Documentação

- [`docs/SPEC_SDD.md`](docs/SPEC_SDD.md): **especificação Spec-Driven Development** (princípios, modelo, requisitos, API, verificação, decisões, estado e como retomar a sessão). Comece por ela.
- [`HANDOFF_CLAUDE_CODE.md`](HANDOFF_CLAUDE_CODE.md): fonte única do escopo (regras de negócio, endpoints, contrato de erro, critérios de aceite, dados de exemplo e pendências).
- [`PLANO_EXECUTAVEL.md`](PLANO_EXECUTAVEL.md): plano por sprint, com prompts, verificações e critérios de aceite.
- [`CLAUDE.md`](CLAUDE.md): orientações para o Claude Code neste repositório.

## Limitações

- **Uso local e de um único usuário:** sem login, sem perfis com permissão e sem acesso de outros computadores. A API só escuta em `127.0.0.1`.
- **Frontend na Vercel depende do backend local:** só funciona no computador onde o backend roda, exige `CORS_ORIGINS` e a permissão do navegador para acessar a rede local; Safari bloqueia. Em outros dispositivos o site abre, mas sem dados.
- **Armazenamento local:** banco SQLite e fotos em disco, backup manual (`.db` + `fotos/`). Hospedar o backend em nuvem exige PostgreSQL e armazenamento de objetos (ver abaixo).
- **Locais e checklist:** a tela Locais lista, cria e edita (não inativa nem exclui); o modelo de checklist (6 itens) é fixo e não tem tela de edição. O CAR é texto livre (nenhum formato é rejeitado) e os telefones aceitam só 10 ou 11 dígitos com DDD.
- **Cópia do empreendimento:** vale a partir do fechamento. Nas inspeções finalizadas antes desta rodada ela reflete o local **de hoje**. A lista de inspeções e os dois CSV (por inspeção e dos itens) mostram o nome do local atual, não a cópia.
- **Número do processo:** texto livre, sem validação de formato e não único. Inspeções criadas antes do campo existir ficam com o número vazio ("—") até serem editadas; o banco antigo é atualizado sozinho na inicialização da API (coluna adicionada sem perder dados).
- **Lista:** mostra até 100 inspeções por consulta (sem paginação na tela).
- **Regras do fluxo:** só se fecha inspeção Em andamento; só se cancela inspeção Aberta; inspeção finalizada ou cancelada não pode ser reaberta nem editada; inspeção agendada para o futuro não aceita item respondido (P1).
- **Fotos:** uma por requisição, JPEG/PNG/WebP, até 5 MB e 20 por inspeção; o arquivo original é regravado só com os pixels (sem metadados). Sem edição, rotação ou câmera. As fotos de exemplo usam uma fonte TrueType do sistema (Arial, DejaVu ou Liberation); sem nenhuma delas, o texto da imagem sai sem acentos.
- **Relatório:** a impressão depende do navegador. "Página X de Y" usa caixas de margem do `@page` e foi conferida no Chromium (Chrome/Edge); o Firefox pode imprimir sem essa numeração. O relatório carrega as imagens originais pela API, então precisa do backend ligado.
- **Sem geração de PDF no servidor, mapa, histórico/auditoria, busca textual ou backup automático** (lista completa na seção 13 do handoff).
- **Testes:** o E2E roda só em Chromium e fora do CI; o site publicado foi validado com a permissão de rede local concedida por script, não pelo pedido real do navegador. Os campos de formulário têm `id`, `name` e `label` (verificado por teste), mas não há auditoria completa de acessibilidade nem testes de carga.
- **Persistência após reiniciar a API (CA22):** validada manualmente na S1A; o E2E recarrega a página, mas não reinicia a API.

## O que mudou na rodada R2

- **Correções de usabilidade:** mensagem orientativa ao fechar inspeção Aberta (botão desabilitado com o motivo); aviso de que só registrar a situação de um item inicia a inspeção; aviso preventivo de agendamento futuro com link para editar; `id`, `name` e `label` em todos os campos; rótulos das datas ("Data de agendamento (planejada)", "Data de realização (vistoria em campo)") e "Checklist concluído em dd/mm/aaaa hh:mm".
- **Empreendimento:** CAR opcional e proprietários (nome e telefone) no cadastro de locais, com a nova tela **Locais** e o cartão **Empreendimento** no detalhe.
- **Cópia no fechamento:** a inspeção finalizada guarda os dados do empreendimento do momento do fechamento.
- **Relatório de vistoria** numerado, com prévia e impressão A4 pelo navegador.
- **Banco existente:** migração automática e idempotente (veja [Atualizando um banco existente](#atualizando-um-banco-existente-migração)).
- **Correções encontradas na verificação:** o rodapé do relatório cobria conteúdo no PDF (passou para as caixas de margem do `@page`); a tabela do checklist deixava linhas órfãs entre páginas; as fotos de exemplo saíam com quadrados no "Í" e no "—".
- **Testes:** backend 229 → 334, frontend 59 → 124 e E2E 11 → 14 passos (mais PDFs do relatório). Os números subiram por causa dos testes novos; nenhum teste existente foi relaxado. Os que mudaram só refletem contrato novo (campo obrigatório, colunas do CSV, rótulos das datas).
- **Depois da rodada (Parte B):** a exportação dos itens do checklist virou o botão **Exportar itens (CSV)** (`GET /api/v1/exportacao/itens.csv`), sem alterar o CSV por inspeção; a regra de vistoria antes do agendamento foi mantida e `respondido_em` ficou para depois. Backend 334 → 348 e frontend 124 → 125 testes.
- **Vercel:** cada push em `main` gera um deploy de produção (a integração com o GitHub está ativa; o push desta rodada gerou um deploy `READY`). Para publicar sem push use `vercel deploy --prod` a partir da raiz (veja a seção da Vercel). `VITE_API_URL` aponta para `127.0.0.1`, então o site só funciona no computador onde o backend roda.

## O que mudou na rodada R4

Dados para a capa da SEMA e corpo do relatório técnico (4 sprints; PR de revisão no GitHub).

- **Dados novos da inspeção:** interessado (órgão, unidade, comarca opcional, requerente), assunto (lista + "Outro"), equipe técnica (1..n), providências (texto e atos com tipo e número) e Nº do relatório na SEMA. O protocolo reaproveita o número do processo e o número interno passou a se chamar **Ref. interna**.
- **Empreendimento e responsável:** nome fantasia (o campo `nome`), endereço (logradouro, município, UF padrão MT, CEP), CPF/CNPJ validado (guardado só com dígitos, exibido com máscara) e endereço para correspondência, com o atalho "Mesmo endereço do empreendimento". Tudo entra na cópia do fechamento.
- **Coordenadas:** exibição em decimal e em GMS (`LAT 11° 46' 34" S | LONG 59° 05' 12" W`, sem sinal e sem 60"); digitação em decimal ou GMS com máscara na tela de Locais, convertida para decimal ao salvar.
- **Regras novas:** a **equipe é obrigatória para fechar**; depois do fechamento só o **número dos atos** e o **Nº do relatório na SEMA** são editáveis (`atualizado_em` registra a edição).
- **Saídas:** página Dados para capa e lavratura (copiar) e corpo do relatório a partir do item 5 (veja as seções acima).
- **Mensagens de validação em português** com o rótulo do campo (`Objetivo: obrigatória`), em vez do texto em inglês do FastAPI.
- **Banco existente:** a migração leve acrescenta as colunas e tabelas novas (veja [Atualizando um banco existente](#atualizando-um-banco-existente-migração)); faça uma cópia de `backend/data/` antes.
- **Testes:** backend 348 → 457, frontend 125 → 159 e E2E 14 → 16 passos. Alguns testes existentes mudaram **por mudança de regra, sem enfraquecer nada**: os auxiliares que fecham inspeção agora informam a equipe; as listas de campos editáveis incluem os campos novos; o contrato de Local/proprietário ganhou campos; o relatório foi reescrito para o corpo a partir do item 5 (os testes dos itens 1 a 4 e do empreendimento no relatório saíram, porque esses dados agora vão na capa). Detalhes em [`R4-capa-sema-corpo-relatorio.md`](docs/evidencias/R4-capa-sema-corpo-relatorio.md).

## Pendências do projeto

- **Documentação M0 não escrita:** `docs/requisitos.md`, `docs/criterios-aceite.md`, as ADRs e `docs/migracao-postgresql.md` não existem; o escopo vale como está no handoff.
- **Matriz CA01–CA85 incompleta:** os critérios cobertos por teste estão nos arquivos de evidência, mas a matriz final (sprint S4) não foi montada.
- **Licença e visibilidade do repositório (P10):** indefinidas.
- **Parte B decidida (23/10/2026):** (B1) a regra de vistoria antes da data agendada **fica como está**, com o aviso preventivo; (B2) o campo `respondido_em` por item foi **adiado** (`data_realizacao` e `fechado_em` cobrem o relatório); (B3) a exportação dos itens do checklist foi **implementada** como arquivo separado. Detalhes em `PB1` a `PB3` no handoff.
- As demais pendências (P1–P9) e os padrões adotados estão na seção 9 do handoff; P11 (versões) está resolvida em [Instalação](#instalação).
