# PLANO_EXECUTAVEL.md — Inspeções Simuladas

Escopo e decisões: **HANDOFF_CLAUDE_CODE.md** (fonte única de verdade). Este plano só organiza a execução.

## Como conduzir (vale para todas as sprints)

1. Abra o Claude Code na raiz do repositório e confirme que `HANDOFF_CLAUDE_CODE.md` está nela.
2. Cole **um único prompt por vez**. Prompts com sufixo A/B são rodadas separadas da mesma sprint.
3. Ao terminar, o Claude Code deve **parar**, listar as evidências e atualizar a seção 10 do handoff. Você revisa, roda os comandos de verificação e só então libera a próxima rodada.
4. Se uma **condição de parada** ocorrer, o Claude Code interrompe e relata em vez de improvisar.
5. Evidências ficam em `docs/evidencias/<sprint>.md` (saída resumida dos comandos, contagem de testes, lista de CAs cobertos).

**Mapa de dependências:** M0 → S0 → S1A → S1B → S2A → S2B → S3 → S4. (S3 depende de S1; pode começar após S1B, mas a ordem acima é a recomendada para uma pessoa só.)

| Sprint | Cobre | CAs principais |
|---|---|---|
| M0 | documentação | — |
| S0 | ambiente, Git, esqueleto | — |
| S1A | banco, domínio, locais, inspeções, itens | CA01–CA14, CA25–CA27, CA29–CA39 (API), CA40 |
| S1B | fotos e anotações (API) | CA41–CA60 (API), CA61–CA68, CA70–CA73 (API) |
| S2A | telas base, lista, nova, checklist | CA02, CA15–CA17, CA34 |
| S2B | observações da vistoria e fotos na UI | CA35–CA41, CA69–CA71 (UI) |
| S3 | indicadores reais, exemplos, CSV | CA18–CA24, CA28, CA58 |
| S4 | testes, correções, README, GitHub | CA01–CA73 completos |
| R1 | cartões clicáveis, editar, nº do processo, novo local | CA74–CA85 |
| R2 | usabilidade, CAR e proprietários, cópia no fechamento, relatório | CA86–CA110 |
| R3 | decisões da Parte B e exportação dos itens do checklist | CA111–CA116 |

---

## M0 — Documentação

**Objetivo.** Transformar o handoff em documentos do repositório, sem escrever código, e fechar as pendências bloqueantes.

**Dependências.** Nenhuma. Decisão humana prévia sobre **P1** (padrão: bloquear) e **P2** (padrão: anotação obrigatória).

**Arquivos prováveis.** `README.md` (rascunho), `docs/requisitos.md`, `docs/criterios-aceite.md`, `docs/adr/ADR-001-arquitetura-mvp.md`, `docs/adr/ADR-002-armazenamento-de-fotos.md`, `docs/migracao-postgresql.md`, `docs/evidencias/M0.md`.

**Prompt para Claude Code (M0)**
```
Leia HANDOFF_CLAUDE_CODE.md por inteiro. Execute SOMENTE a sprint M0 (documentação). Não crie código nem pastas de backend/frontend.
Tarefas:
1. Crie docs/requisitos.md com visão do produto, perfis, RF01–RF06 (RF01 cadastrar, RF02 registrar itens, RF03 fechar, RF04 consultar, RF05 indicadores, RF06 persistência/exportação; fotos e observações da vistoria como extensões de RF02/RF04/RF06), regras RN01–RN34, entidades, endpoints, contrato de erros e limites do MVP, copiando fielmente o handoff.
2. Crie docs/criterios-aceite.md com CA01–CA73 (numeração estável) em formato Dado/Quando/Então, agrupados como na seção 11 do handoff, indicando a camada que valida cada um (domínio, persistência, serviço, API, front, manual).
3. Crie ADR-001 e ADR-002 (status, contexto, decisão, alternativas, consequências) e docs/migracao-postgresql.md.
4. Crie um README.md inicial (objetivo, stack, aviso de dados fictícios, "como rodar: a definir na S0/S4").
5. Liste em docs/evidencias/M0.md qualquer contradição ou lacuna que encontrar no handoff (sem resolvê-la por conta própria).
6. Atualize a seção 10 do handoff e faça commit "docs: documentação inicial (M0)".
PARE ao concluir e liste os arquivos criados e as contradições encontradas.
```

**Comandos de verificação**
```
ls docs docs/adr
grep -c "^RN" docs/requisitos.md        # ou conferir manualmente RN01..RN34
grep -o "CA[0-9][0-9]" docs/criterios-aceite.md | sort -u | wc -l   # esperado: 73
git log --oneline -1
```

**Critérios de aceite**
- Os 6 documentos existem e estão em português.
- 34 regras (RN01–RN34) e 73 CAs presentes, sem renumeração.
- Cada CA indica a camada de validação.
- Nenhum arquivo de código foi criado.
- Contradições listadas em `docs/evidencias/M0.md`.

**Evidências.** `docs/evidencias/M0.md` com contagens (RN, CA), lista de arquivos e lacunas encontradas; hash do commit.

**Condição de parada.** Parar se o handoff e os documentos divergirem em alguma regra (relatar, não escolher), ou se faltar informação para um CA (registrar como lacuna).

---

## S0 — Estrutura, ambiente e Git

**Objetivo.** Repositório rodável e vazio de regras: esqueleto de pastas, ambientes backend/frontend, `health` respondendo, CI mínimo, Git organizado.

**Dependências.** M0 concluída; Python e Node instalados (versões: pendência P11).

**Arquivos prováveis.** `.gitignore`, `backend/pyproject.toml`, `backend/.env.example`, `backend/app/{main,config,database,clock,errors}.py`, `backend/tests/{conftest.py,api/test_health.py}`, `frontend/{package.json,vite.config.ts,src/main.tsx,src/App.tsx}`, `.github/workflows/ci.yml`, README (seção "Ambiente").

**Prompt para Claude Code (S0)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 2, 14, 15). Execute SOMENTE a sprint S0.
1. Inicialize o Git (branch main) se ainda não existir; crie .gitignore conforme seção 14.
2. Backend: crie a estrutura de pastas da seção 14 (pastas vazias com __init__ quando necessário), pyproject com FastAPI, uvicorn, SQLAlchemy, pydantic, python-multipart, Pillow, pytest, httpx. Implemente apenas: app FastAPI com GET /api/v1/health (retorna {"status":"ok"}), config lendo DATABASE_URL (padrão sqlite em backend/data/inspecoes.db), database.py com engine/sessão e PRAGMA foreign_keys=ON para SQLite, clock.py com "hoje" injetável, errors.py com o contrato de erro único (apenas a base: exceção de negócio + handler que gera {"erro":{codigo,mensagem,detalhes}}). Nenhum modelo de domínio ainda.
3. Teste: um teste de API do /health e um teste do clock (fixo em 2026-10-23).
4. Frontend: Vite + React + TypeScript + TanStack Query + Vitest + Testing Library; proxy /api -> http://127.0.0.1:8000; App mostrando "Inspeções Simuladas" e o status do /health; 1 teste de renderização.
5. CI (GitHub Actions): jobs de pytest e de npm test + npm run build.
6. README: seção "Ambiente" com os comandos reais que você usou.
7. Commits pequenos (Conventional Commits). Atualize a seção 10 do handoff e crie docs/evidencias/S0.md.
NÃO implemente modelos, rotas de negócio ou telas. PARE ao concluir e mostre a saída dos comandos de verificação.
```

**Comandos de verificação**
```
cd backend && python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"        # ou o comando que o projeto documentar
pytest -q
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
curl -s http://127.0.0.1:8000/api/v1/health
cd ../frontend && npm install && npm test -- --run && npm run build
npm run dev   # abrir http://localhost:5173 e ver o status do health
git status --short && git log --oneline
```

**Critérios de aceite**
- `pytest -q` verde (≥ 2 testes); `npm test` e `npm run build` verdes.
- `GET /api/v1/health` → 200 `{"status":"ok"}`; a página no Vite mostra o status via proxy.
- `.gitignore` impede `*.db`, `.env`, `.venv`, `node_modules`.
- API escuta em `127.0.0.1`.
- Árvore de pastas coincide com a seção 14.

**Evidências.** `docs/evidencias/S0.md` com saída de `pytest -q`, do `curl` e do build; captura ou descrição da página; `git log --oneline`.

**Condição de parada.** Parar se versões de Python/Node não forem compatíveis (relatar a versão encontrada), se a instalação de dependências falhar por rede, ou se for necessário introduzir qualquer regra de negócio para "fazer funcionar".

---

## S1A — Banco + API CRUD (locais, inspeções, itens)

**Objetivo.** Persistência real e API completa do fluxo central: cadastrar → registrar itens → editar → cancelar → fechar, com todas as regras e erros.

**Dependências.** S0. Decisão **P1** registrada.

**Arquivos prováveis.** `backend/app/models/{local,inspecao,item_inspecao,modelo_item}.py`, `schemas/`, `domain/{resultado,transicoes,datas,coordenadas,texto}.py`, `repositories/`, `services/{inspecao_service,item_service}.py`, `routers/{locais,inspecoes,itens}.py`, `tests/{unit,service,api}/`, `tests/fixtures/seed_exemplo.py`, `docs/evidencias/S1A.md`.

**Prompt para Claude Code (S1A)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 3, 4, 5, 6, 9, 11, 12). Execute SOMENTE a sprint S1A. Não implemente fotos, indicadores, exemplos via endpoint, CSV nem frontend.
Trabalhe em camadas e nesta ordem, com testes em cada uma:
1. domain (funções puras, testes unitários): cálculo do resultado (RN06), transições (RN08), regras de data (RN02, RN13), faixa de coordenadas (RN11), saneamento de texto (trim, vazio->nulo, limite).
2. models + constraints (CHECKs de coordenadas, datas, resultado só em FINALIZADA, motivo de cancelamento, tamanhos; FKs; únicos; CASCADE) e testes de persistência em SQLite em memória com foreign_keys=ON. Criação das tabelas por create_all.
3. services: cadastrar inspeção (código INS-NNN, 6 itens do modelo), registrar item (1º item: ABERTA->EM_ANDAMENTO e preenche data_realizacao; aplique o padrão da pendência P1), adicionar/remover item avulso, editar por status (RN14, observacoes_vistoria RN16-RN19), cancelar, fechar (RN04, RN05, RN06; só EM_ANDAMENTO conforme P3). Testes de serviço usando a fixture de seed (seção 12) com clock fixo em 2026-10-23.
4. routers + contrato de erro: endpoints de locais, inspecoes (POST, GET lista com filtros/paginação, GET detalhe, PATCH, cancelar, fechar) e itens, exatamente como na seção 5, com todos os códigos da seção 6 que se aplicam. Testes de API com TestClient.
5. Faça um seed de teste (fixture, NÃO endpoint) com os 4 locais, 6 itens do modelo e as 5 inspeções.
Regras: nenhuma regra de negócio em routers; não enfraqueça testes; se uma regra for ambígua, consulte a seção 9 e, se não estiver lá, PARE e pergunte.
Ao final: pytest -q verde, docs/evidencias/S1A.md com a lista de CAs cobertos por teste (id do CA -> nome do teste), atualização da seção 10 e commits por camada. PARE e aguarde revisão.
```

**Comandos de verificação**
```
cd backend && pytest -q
pytest -q tests/unit && pytest -q tests/service && pytest -q tests/api
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
curl -s -X POST http://127.0.0.1:8000/api/v1/locais -H "Content-Type: application/json" \
  -d '{"nome":"Teste","municipio":"X","tipo":"Y","latitude":-25.0,"longitude":-58.0}'   # espera 422 COORDENADA_FORA_DE_MT
curl -s "http://127.0.0.1:8000/api/v1/inspecoes?status=EM_ANDAMENTO"
sqlite3 backend/data/inspecoes.db ".schema inspecao"   # conferir CHECKs (opcional)
```

**Critérios de aceite**
- Todos verdes: unit, persistência, serviço e API.
- CAs cobertos (mapeados em `S1A.md`): CA01–CA14, CA15–CA17, CA25–CA27, CA29–CA40 (parte API) e CA21 (via consulta no teste).
- Contrato de erro idêntico à seção 6 (código, mensagem, detalhes).
- Fechamento bloqueado devolve um detalhe por item problemático (CA09/CA10).
- INS-001..INS-005 reproduzem resultados esperados (Aprovada / ressalvas / Reprovada).
- Nenhum arquivo de foto, endpoint de indicadores ou UI criado.

**Evidências.** Saída de `pytest -q` (contagem), tabela CA → teste, trecho de uma resposta de erro real de fechamento bloqueado, `git log`.

**Condição de parada.** Parar se: (a) uma regra exigir decisão fora do handoff; (b) um teste só passar relaxando uma constraint; (c) surgir necessidade de escopo novo (hora, histórico, login). Registrar em `S1A.md` e aguardar.

---

## S1B — API de fotos e anotações

**Objetivo.** Upload, listagem, arquivo, edição e exclusão de fotos com anotação obrigatória, armazenamento em disco e consistência.

**Dependências.** S1A concluída e revisada.

**Arquivos prováveis.** `models/foto_vistoria.py`, `domain/imagem.py`, `storage/arquivos.py`, `repositories/foto_repository.py`, `services/foto_service.py`, `routers/{fotos,utilitarios}.py` (apenas `verificar-fotos` aqui), `schemas/foto.py`, `tests/fixtures/imagens.py` (gera imagens em memória), `tests/{unit,service,api}/test_foto*.py`, `docs/evidencias/S1B.md`.

**Prompt para Claude Code (S1B)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 2 [ADR-002], 3, 4 [RN20–RN34], 5, 6, 11, 12). Execute SOMENTE a sprint S1B (fotos). Não toque em frontend, indicadores nem CSV.
1. domain/imagem.py: validação por CONTEÚDO (JPEG/PNG/WebP), limites (5.242.880 bytes), hash SHA-256, geração de miniatura (lado maior 320 px) e remoção de EXIF; saneamento da anotação (1..1000 após trim) e legenda (≤200). Testes unitários usando imagens geradas em código (nunca imagens reais).
2. storage/arquivos.py: interface + implementação em disco (backend/data/fotos/{inspecao_id}/original|miniatura/{uuid}.ext), caminhos gerados pelo sistema, nunca vindos do usuário. Testes com tmp_path.
3. model FotoVistoria com constraints e índices (seção 3); testes de persistência (CASCADE, SET NULL, único inspecao+hash).
4. foto_service: respeitar a ordem de validação da seção 6 (estado 409 -> campos 422/413/415 -> limite/duplicidade 409 -> gravar), RN28 (arquivo antes do registro; compensar em falha), RN23–RN24, RN27, RN29, RN30; edição de anotação/legenda/item/ordem.
5. routers: POST (multipart, uma foto por requisição), GET lista/detalhe, GET arquivo (miniatura|original, nosniff, mime gravado), PATCH, DELETE e GET /utilitarios/verificar-fotos. Incluir fotos e contagens no detalhe da inspeção e qtd_fotos na lista.
6. Testes de API com pasta temporária e o conjunto de imagens da seção 12 (JPEG, PNG, WebP, EXIF/GPS, 5.242.880/5.242.881, GIF, texto renomeado, vazio, duplicata, 21 imagens, nome com <script>).
Não enfraqueça testes. Ao final: pytest -q verde, docs/evidencias/S1B.md com CA -> teste (CA42–CA57, CA59, CA60–CA68, CA70, CA72, CA73 na camada API/serviço), seção 10 atualizada, commits por camada. PARE.
```

**Comandos de verificação**
```
cd backend && pytest -q
pytest -q -k foto
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
curl -s -X POST "http://127.0.0.1:8000/api/v1/inspecoes/4/fotos" -F "arquivo=@/caminho/img_ficticia.jpg" -F "anotacao=Teste de anotação"
curl -s -X POST "http://127.0.0.1:8000/api/v1/inspecoes/4/fotos" -F "arquivo=@/caminho/img_ficticia.jpg"        # espera 422 sem anotação
curl -s -o /dev/null -w "%{http_code} %{content_type}\n" "http://127.0.0.1:8000/api/v1/inspecoes/4/fotos/1/arquivo?versao=miniatura"
curl -s http://127.0.0.1:8000/api/v1/utilitarios/verificar-fotos
ls backend/data/fotos/4/original backend/data/fotos/4/miniatura
```

**Critérios de aceite**
- Suíte inteira verde (S1A não regride).
- 415 para GIF e texto renomeado; 413 em 5.242.881 B; 409 na 21ª foto e na duplicata; 422 sem anotação, e **nenhum arquivo criado em disco** nesses casos.
- EXIF/GPS ausente no original e na miniatura (teste lê o arquivo gravado).
- Foto em FINALIZADA/CANCELADA → 409; consulta continua funcionando.
- Excluir foto remove registro, original e miniatura.
- `verificar-fotos` acusa arquivo apagado e arquivo solto; zero inconsistências em banco limpo.
- Anotação não altera resultado nem fechamento (CA72).

**Evidências.** Saída de `pytest -q`; tabela CA → teste; listagem das pastas de fotos antes/depois de uma exclusão; resposta real do `verificar-fotos`.

**Condição de parada.** Parar se Pillow não instalar ou não conseguir remover EXIF de algum formato; se a ordem de validação conflitar com RN28; ou se surgir pedido de captura por câmera, rotação ou compressão (fora do escopo).

---

## S2A — Frontend e integração (base, lista, nova, checklist)

**Objetivo.** Interface funcional para o fluxo central consumindo a API real, com estados de carregando/vazio/erro.

**Dependências.** S1B (API estável). Tipos TypeScript derivados dos contratos reais.

**Arquivos prováveis.** `frontend/src/api/{cliente,tipos,erros}.ts`, `hooks/{useInspecoes,useInspecao}.ts`, `pages/{InspecoesPage,NovaInspecaoPage,InspecaoDetalhePage}.tsx`, `components/{TabelaInspecoes,ItemChecklist,ModalFechar,ModalCancelar,MensagemErro}.tsx`, `utils/{formatarData,rotulos}.ts`, `tests/`, `docs/evidencias/S2A.md`.

**Prompt para Claude Code (S2A)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 5, 6, 8, 11). Execute SOMENTE a sprint S2A. Não implemente observações da vistoria, fotos nem o painel de indicadores (apenas um placeholder de rota "/" ).
1. api/: cliente HTTP único, tipos TS espelhando os contratos reais da API (leia as respostas reais ou os schemas do backend), conversão de erros para {codigo, mensagem, detalhes}.
2. Telas: Lista (/inspecoes) com colunas e filtros de status e período; Nova (/inspecoes/nova) com seleção de local mostrando lat/long somente leitura; Detalhe (/inspecoes/:id) com cabeçalho (status, duas datas, local), checklist (situação + observação por item), item avulso, modais Fechar e Cancelar, e modo somente leitura em FINALIZADA/CANCELADA.
3. Erros: componente único MensagemErro; no fechamento bloqueado destacar os itens citados em detalhes; tratar P1 mostrando a mensagem da API.
4. Datas em dd/mm/aaaa na interface e ISO na API; "—" para valores vazios.
5. Testes Vitest/Testing Library com a API simulada: formulário (obrigatórios), checklist, erro de fechamento, estados vazio/carregando/erro, somente leitura.
6. Regras de negócio NÃO podem ser duplicadas no front (apenas validação de campos obrigatórios e exibição).
Ao final: npm test e npm run build verdes, roteiro manual contra a API real com os dados de teste (carregue-os via fixture/SQL ou chamadas da API, pois o endpoint de exemplos só existe na S3), docs/evidencias/S2A.md, seção 10 atualizada. PARE.
```

**Comandos de verificação**
```
# terminal 1
cd backend && source .venv/bin/activate && uvicorn app.main:app --host 127.0.0.1 --port 8000
# terminal 2
cd frontend && npm test -- --run && npm run build && npm run dev
# manual: http://localhost:5173/inspecoes
```

**Critérios de aceite**
- Testes de front verdes e build sem erros.
- Roteiro manual com a API real: criar inspeção (agendamento futuro aceito); registrar itens; tentar fechar com pendências e ver os itens destacados; fechar com tudo respondido e ver resultado; cancelar uma Aberta com motivo.
- Filtros funcionam (CA15, CA16); detalhe mostra todos os itens (CA17) e as duas datas (CA34).
- Em INS finalizada/cancelada não há botões de edição.
- Nenhuma regra de resultado/transição no código do front.

**Evidências.** Saída de `npm test` e `npm run build`; passos do roteiro manual com resultado observado; prints ou descrição das telas; `docs/evidencias/S2A.md`.

**Condição de parada.** Parar se o contrato da API divergir dos tipos (corrigir contrato é decisão do dono do produto), se for preciso duplicar regra no front, ou se algo exigir mudança no backend (registrar e aguardar).

---

## S2B — Observações da vistoria e fotos na interface

**Objetivo.** Completar a tela de execução com `observacoes_vistoria` e a galeria de fotos com anotação obrigatória.

**Dependências.** S2A revisada; API de fotos da S1B.

**Arquivos prováveis.** `components/{BlocoObservacoesVistoria,UploadFotos,GaleriaFotos,VisualizadorFoto}.tsx`, ajustes em `InspecaoDetalhePage` e `ModalFechar`, `tests/`, `docs/evidencias/S2B.md`.

**Prompt para Claude Code (S2B)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 4 [RN16–RN19, RN20–RN34], 5, 6, 8, 11). Execute SOMENTE a sprint S2B.
1. Bloco "Observações da vistoria (o que foi visualizado)": área de texto com contador x/2000, botão salvar; somente leitura em FINALIZADA/CANCELADA; vazio mostra "—"; texto exibido como texto puro com quebras preservadas (sem HTML).
2. Fotos: seleção múltipla/arrastar; lista de PENDENTES, cada uma com miniatura, campo "O que foi observado nesta foto?" (obrigatório, x/1000), legenda e item opcionais; botão "Enviar" desabilitado até todas terem anotação; envio sequencial, uma foto por requisição, com progresso e erro por arquivo; falha parcial preserva a anotação da que falhou.
3. Galeria com miniatura + trecho da anotação + selo do item; visualizador com original, anotação completa, anterior/próxima, editar anotação/legenda/vínculo e excluir (com confirmação) apenas em ABERTA/EM_ANDAMENTO.
4. Selo de quantidade de fotos por item do checklist; modal Fechar com resumo das observações, "Fotos anexadas: n" e aviso não bloqueante para item NC sem foto.
5. Escapar nome_original, legenda e anotação.
6. Testes: botão desabilitado com anotação faltando (CA69), falha parcial (CA70), <script> literal (CA71), contador/limite 2000, somente leitura nos estados finais.
Ao final: npm test e npm run build verdes; roteiro manual com 3 imagens de teste (uma inválida); docs/evidencias/S2B.md; seção 10. PARE.
```

**Comandos de verificação**
```
cd frontend && npm test -- --run && npm run build
# manual com backend ligado: abrir uma inspeção em andamento, enviar 3 arquivos (2 válidos + 1 GIF),
# reiniciar a API, recarregar a página e conferir fotos e anotações
ls backend/data/fotos/<id>/original
```

**Critérios de aceite**
- CA35–CA41 verificados na UI (gravar texto sem mudar status; 2000/2001; só espaços; imutável nos estados finais; `<script>` literal).
- CA69 e CA70 comprovados em teste e no roteiro manual.
- Anotação e fotos permanecem após reiniciar a API (CA56, CA66).
- Em FINALIZADA/CANCELADA: galeria consultável, sem botões de envio/edição/exclusão.
- Nenhum recurso fora do escopo (rotação, marcação, câmera).

**Evidências.** `npm test`/build; descrição do roteiro manual com o resultado de cada passo; arquivos conferidos em disco; `docs/evidencias/S2B.md`.

**Condição de parada.** Parar se a UI exigir comportamento não previsto (ex.: envio em lote em uma única requisição), se aparecerem erros 5xx da API (reportar à S1B), ou se testes só passarem ocultando validação.

---

## S3 — Dashboard com dados reais

**Objetivo.** Painel com os 3 indicadores vindos do banco, mais carga de exemplos e exportação CSV, completando RF05 e RF06.

**Dependências.** S1B e S2B.

**Arquivos prováveis.** `backend/app/services/{indicador_service,seed_service,export_service}.py`, `routers/{indicadores,utilitarios,exportacao}.py`, `backend/app/seed/` (gerador das 9 imagens fictícias), `tests/{service,api}/`, `frontend/src/pages/PainelPage.tsx`, `components/CartaoIndicador.tsx`, `hooks/useIndicadores.ts`, `docs/evidencias/S3.md`.

**Prompt para Claude Code (S3)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 5, 7, 11, 12). Execute SOMENTE a sprint S3.
Backend:
1. GET /api/v1/indicadores com UMA consulta de agregação condicional (seção 7): Inspeções (exclui CANCELADA), Pendências (ABERTA, EM_ANDAMENTO), Finalizadas. Resposta {inspecoes, pendencias, finalizadas, gerado_em}.
2. POST /api/v1/utilitarios/carregar-exemplos: grava 4 locais, 6 itens do modelo, 5 inspeções (status, datas, itens, observacoes_vistoria) e 9 fotos fictícias GERADAS POR PROGRAMA com Pillow (texto "FOTO FICTÍCIA — INS-00X #n") com as anotações exatas da seção 12; 409 BANCO_JA_POVOADO se já houver dados.
3. GET /api/v1/exportacao/inspecoes.csv com as colunas da seção 5 (aspas e quebras de linha corretas).
Frontend:
4. Painel (/) com 3 cartões que usam os dados reais, atalhos "Nova inspeção" e "Ver pendências" (lista já filtrada), botão "Carregar exemplos" (confirma e trata 409) e botão "Exportar CSV". Invalidar o cache dos indicadores após qualquer gravação (fechar, cancelar, cadastrar) para atualizar sem recarregar a página (CA19).
Testes: invariante Pendências+Finalizadas=Inspeções após cada operação (CA21); exemplos => 5/2/3 (CA18); fechar INS-004 => 1/4 (CA19); cancelar INS-005 => reduz Inspeções e Pendências em 1 (CA20); CSV com campo contendo aspas, ponto e vírgula e quebra de linha (CA41); lista com 3/2/2/2/0 fotos (CA58).
Ao final: pytest -q e npm test verdes, roteiro manual, docs/evidencias/S3.md, seção 10. PARE.
```

**Comandos de verificação**
```
cd backend && pytest -q
rm -f data/inspecoes.db && rm -rf data/fotos      # banco novo (apenas para teste local)
uvicorn app.main:app --host 127.0.0.1 --port 8000 &
curl -s -X POST http://127.0.0.1:8000/api/v1/utilitarios/carregar-exemplos
curl -s http://127.0.0.1:8000/api/v1/indicadores            # esperado 5 / 2 / 3
curl -s -X POST http://127.0.0.1:8000/api/v1/utilitarios/carregar-exemplos   # esperado 409
curl -s -o inspecoes.csv http://127.0.0.1:8000/api/v1/exportacao/inspecoes.csv && head -3 inspecoes.csv
sqlite3 data/inspecoes.db "SELECT status, COUNT(*) FROM inspecao GROUP BY status;"
cd ../frontend && npm test -- --run && npm run build
```

**Critérios de aceite**
- Exemplos → indicadores 5/2/3 (CA18); os números do painel coincidem com `SELECT ... GROUP BY status` no banco.
- Fechar INS-004 → 1/4 sem recarregar (CA19); cancelar INS-005 → ajuste correto (CA20); invariante CA21 sempre válida.
- Segunda carga → 409; nenhum dado duplicado.
- CSV com as colunas definidas e campos especiais corretos (CA23, CA28, CA41); `qtd_fotos` = 3/2/2/2/0 (CA58).
- Banco novo + carga de exemplos reproduz todas as inspeções, observações e as 9 fotos (CA24).

**Evidências.** Respostas reais de `/indicadores` antes/depois de cada operação; trecho do CSV; resultado do `GROUP BY`; `docs/evidencias/S3.md`.

**Condição de parada.** Parar se o painel exigir gráfico/relatório (fora do escopo), se os números do painel divergirem do banco (corrigir a consulta, não o teste), ou se a geração de imagens depender de arquivos reais.

---

## S4 — Testes, correções, README e GitHub

**Objetivo.** Fechar o MVP: cobertura dos 73 CAs, correções, README executável do zero, repositório publicado com CI verde.

**Dependências.** S3 revisada. Pendências **P10** (licença/visibilidade) e **P11** (versões) decididas.

**Arquivos prováveis.** `docs/evidencias/matriz-ca.md`, correções pontuais em qualquer camada, `README.md` final, `docs/migracao-postgresql.md` (revisão), `.github/workflows/ci.yml`, `HANDOFF_CLAUDE_CODE.md` (seção 10 final).

**Prompt para Claude Code (S4)**
```
Leia HANDOFF_CLAUDE_CODE.md (seções 0, 9, 10, 11, 15). Execute SOMENTE a sprint S4. Não adicione funcionalidades.
1. Monte docs/evidencias/matriz-ca.md: para cada CA01–CA73, o(s) teste(s) automatizado(s) que o cobrem OU o passo do roteiro manual. Liste CAs sem cobertura e escreva os testes que faltam.
2. Rode toda a suíte (pytest -q; npm test; npm run build). Corrija falhas pela causa; relate cada correção em docs/evidencias/S4.md. Não enfraqueça testes.
3. Execute o roteiro de fumaça completo (banco novo -> carregar exemplos -> indicadores 5/2/3 -> fechar INS-004 -> cancelar INS-005 -> enviar 2 fotos com anotação -> reiniciar API -> conferir persistência -> exportar CSV -> verificar-fotos) e registre o resultado de cada passo.
4. README final: objetivo, aviso de dados fictícios, requisitos (versões), instalação do zero, como rodar backend e frontend, como carregar exemplos, como testar, estrutura de pastas, backup (.db + data/fotos), limites do MVP, caminho PostgreSQL, e a lista de pendências abertas.
5. Revise .gitignore (nenhum .db, .env ou foto no repositório), ci.yml (pytest, npm test, build) e confirme que o repositório clona e roda do zero seguindo apenas o README.
6. GitHub: prepare a publicação (remoto, branch main protegida se aplicável, tag v0.1.0-mvp). Só execute push/criação de repositório se eu confirmar; caso contrário, deixe os comandos prontos no README.
7. Atualize a seção 10 do handoff (todas as sprints marcadas) e a seção 9 (pendências resolvidas/abertas). PARE e entregue o relatório final.
```

**Comandos de verificação**
```
git clone <repo> /tmp/teste-limpo && cd /tmp/teste-limpo     # seguir SOMENTE o README
cd backend && pytest -q
cd ../frontend && npm test -- --run && npm run build
git ls-files | grep -E "\.db$|\.env$|data/fotos" || echo "ok: nada sensível versionado"
git tag -l && git log --oneline | head -20
```
(CI: verificar o workflow verde na aba Actions após o push.)

**Critérios de aceite**
- Matriz CA01–CA73 sem lacunas (cada CA tem teste automatizado ou passo manual registrado).
- Suíte backend e front verde; build sem erros; CI verde no GitHub.
- Roteiro de fumaça executado com todos os passos aprovados (critério de pronto do MVP).
- Clone limpo roda seguindo apenas o README.
- Nenhum arquivo sensível versionado; nenhuma foto/`.db` no Git.
- Pendências P1–P11 com status explícito.

**Evidências.** `matriz-ca.md`, `S4.md` (correções + roteiro de fumaça), saída das suítes, link ou captura do CI, `git log`/tag.

**Condição de parada.** Parar se algum CA não puder ser verificado (reportar, não marcar como atendido), se o clone limpo falhar, ou se for preciso mudar escopo para fechar o MVP. Push/publicação só com confirmação explícita.

---

## R1 — Melhorias pós-uso (cartões clicáveis, editar, número do processo, novo local)

**Objetivo.** Atender o primeiro feedback de uso: cartões do Painel que listam a categoria, botão e página de edição, número do processo (obrigatório, texto livre, com filtro) e criação de local pela tela de nova inspeção.

**Dependências.** S3 concluída. Decisões do usuário: número do processo obrigatório em texto livre e filtro por número.

**Arquivos prováveis.** `backend/app/{database,models/inspecao,services/inspecao_service,repositories/inspecao_repository,routers/inspecoes,schemas/inspecao,services/export_service}.py`, `frontend/src/pages/{PainelPage,InspecoesPage,EditarInspecaoPage,NovaInspecaoPage,InspecaoDetalhePage}.tsx`, `frontend/src/components/ModalNovoLocal.tsx`, `e2e/tests/fluxo.spec.ts`, `docs/evidencias/R1-melhorias.md`.

**Prompt para Claude Code (R1)**
```
Leia HANDOFF_CLAUDE_CODE.md (RN14, RN35–RN38, seções 3, 5, 8). Execute SOMENTE a rodada R1.
1. Backend: numero_processo obrigatório (texto livre ≤60, editável em Aberta/Em andamento), migração leve da coluna, status repetível e filtro numero_processo em GET /inspecoes, campos_editaveis no detalhe, coluna numero_processo no CSV.
2. Frontend: cartões do Painel como links para a lista da categoria (Inspeções exclui canceladas); coluna e busca por processo na lista; botão e página Editar guiados por campos_editaveis; campo número do processo e botão "+ Novo local" em Nova inspeção.
3. Testes de serviço, API, Vitest e E2E (com telas). Não relaxe testes existentes: explique qualquer número diferente.
4. Atualize README e HANDOFF (seção 16) e crie docs/evidencias/R1-melhorias.md. PARE.
```

**Comandos de verificação**
```
cd backend && pytest -q
cd ../frontend && npm test -- --run && npm run build
cd ../e2e && npx playwright test
```

**Critérios de aceite.** CA74–CA85 (seção 11 do handoff). Cada cartão abre a lista da categoria e o total coincide com o contador; número do processo obrigatório; banco antigo migrado sem perder dados.

**Evidências.** `docs/evidencias/R1-melhorias.md`; telas em `docs/evidencias/telas/`.

**Condição de parada.** Parar se o contrato do `POST /inspecoes` precisar mudar além do campo novo, ou se a migração do banco existente exigir recriar tabelas.

---

## R2 — Usabilidade, empreendimento (CAR e proprietários), cópia no fechamento e relatório

**Objetivo.** Corrigir os problemas achados no teste manual (Parte A), acrescentar CAR e proprietários aos locais com tela própria, congelar os dados do empreendimento no fechamento e gerar um relatório de vistoria numerado e imprimível.

**Dependências.** R1 concluída. Decisões do usuário: CAR em texto livre (nunca rejeita formato); legado preenchido na inicialização; `VITE_API_URL` mantido em `127.0.0.1`. A Parte B (regra de vistoria antes do agendamento, `respondido_em`, exportação dos itens) **não** faz parte desta rodada: ver `PB1`–`PB3` na seção 9 do handoff.

**Arquivos prováveis.** Backend: `domain/{orientacoes,contato,relatorio}.py`, `models/{proprietario,contador_relatorio,local,inspecao}.py`, `services/{local_service,empreendimento_service,numeracao_service,relatorio_service,migracao_dados,inspecao_service}.py`, `schemas/{local,relatorio,inspecao}.py`, `routers/inspecoes.py`, `database.py` (migração leve), `seed/`. Frontend: `components/{FormularioLocal,ModalNovoLocal,ItemChecklist,UploadFotos,...}.tsx`, `pages/{LocaisPage,LocalFormPage,RelatorioPage,InspecaoDetalhePage,EditarInspecaoPage}.tsx`, `estilos.css` (impressão). E2E e evidências.

**Prompt para Claude Code (R2)**
```
Leia HANDOFF_CLAUDE_CODE.md (RN39–RN46, seções 3, 5, 8, 9 e 11). Execute SOMENTE a rodada R2, na ordem e com um commit por assunto:
1. fix (Parte A): A1 mensagem orientativa ao fechar inspeção Aberta (código TRANSICAO_INVALIDA, botão desabilitado com o motivo); A2 aviso de que só registrar a situação inicia a inspeção; A3 aviso preventivo de agendamento futuro com link para editar e situações desabilitadas; A4 id, name e label em todos os campos (com teste genérico); A5 rótulos das datas e "Checklist concluído em dd/mm/aaaa hh:mm".
2. feat (C1): Local com numero_car (maiúsculas, trim, ≤60, nunca rejeita formato) e proprietarios (tabela própria, nome ≤120, telefone só dígitos 10/11 com DDD, exibido (65) 99999-9999); tela Locais (listar, cadastrar, editar) e cartão Empreendimento no detalhe; seed e testes só com dados fictícios; migração leve.
3. feat (C2): ao fechar, gravar na mesma transação a cópia dos dados do empreendimento; a finalizada usa a cópia; antes do fechamento usa o Local atual; preencher o legado na inicialização.
4. feat (C3): numero_relatorio NNNN/AAAA (sequencial por ano, único, nunca reutilizado), GET /inspecoes/{id}/relatorio, página /inspecoes/:id/relatorio com prévia sem número e marca, CSS @media print (A4, sem menu/botões, rodapé e Página X de Y em todas as páginas, no máximo 2 fotos por página). Sem biblioteca de PDF no backend.
5. docs: README, PLANO_EXECUTAVEL, HANDOFF, evidências e telas.
Antes de cada commit rode backend, frontend e E2E. Não relaxe testes. Explique todo número diferente. Confira que nenhum .env*, backend/data, dist, node_modules, .venv, test-results ou .db entra no commit. PARE e entregue o resumo.
```

**Comandos de verificação**
```
cd backend && pytest -q
cd ../frontend && npm test -- --run && npm run build
cd ../e2e && npx playwright test        # também gera docs/evidencias/relatorio-INS-004.pdf e relatorio-previa-INS-005.pdf
git status --short && git log --oneline -10
```
Conferir os PDFs gerados: rodapé e "Página X de Y" em todas as páginas, no máximo 2 fotos por página sem corte, prévia com a marca no topo de todas as páginas e sem número.

**Critérios de aceite.** CA86–CA110 (seção 11 do handoff). Em especial: editar o Local depois do fechamento não muda a finalizada; numeração sem repetição inclusive na virada de ano; prévia nunca mostra número e não consome número; dados 100% fictícios no seed, testes e capturas.

**Evidências.** `docs/evidencias/R2-melhorias.md` (CA → teste, defeitos encontrados), telas em `docs/evidencias/telas/`, PDFs do relatório e resumo de cada suíte (334 backend, 124 frontend, 14 E2E na última execução).

**Condição de parada.** Parar se aparecer conflito no `git pull --rebase` (mostrar os arquivos, sem resolver); se o push falhar por credencial (informar o erro e o comando, sem gravar token); se algum arquivo proibido aparecer no commit; ou se for preciso rejeitar um formato de CAR (exige confirmação do usuário). Não implementar a Parte B sem decisão.

---

## R3 — Decisões da Parte B e exportação dos itens do checklist

**Objetivo.** Registrar as decisões do usuário (B1 manter a regra atual, B2 adiar `respondido_em`) e implementar a B3: um CSV separado com uma linha por item do checklist, sem alterar o CSV por inspeção.

**Dependências.** R2 concluída.

**Arquivos prováveis.** `backend/app/services/export_itens_service.py`, `backend/app/routers/painel.py`, `backend/tests/api/test_exportacao_itens.py`, `frontend/src/api/api.ts`, `frontend/src/pages/PainelPage.tsx`, `e2e/tests/fluxo.spec.ts`, `docs/evidencias/R3-exportacao-itens.md`.

**Prompt para Claude Code (R3)**
```
B1: manter a regra atual (a). B2: adiar. B3: implementar como proposto, com testes, commit e push seguindo a Parte D.
1. GET /api/v1/exportacao/itens.csv: uma linha por item de cada inspeção (inclui canceladas e itens avulsos), delimitador ";", UTF-8 com BOM, texto livre protegido contra fórmulas. Colunas: codigo_inspecao, numero_processo, local, status_inspecao, resultado_inspecao, item_numero, item_descricao, critico (sim/nao), situacao, observacao, origem, qtd_fotos. Não altere /exportacao/inspecoes.csv.
2. Botão "Exportar itens (CSV)" no Painel, ao lado de "Exportar CSV".
3. Testes de API (formato, conteúdo, caracteres especiais, fórmulas, fotos por item, CSV atual inalterado), Vitest e E2E (download e conferência do conteúdo).
4. Atualize README, PLANO, HANDOFF (PB1–PB3, RN47, CA111–CA116) e as evidências. Antes de cada commit rode backend, frontend e E2E e confira que nenhum arquivo proibido entra. fetch, pull --rebase se necessário, push sem --force.
```

**Comandos de verificação**
```
cd backend && pytest -q
cd ../frontend && npm test -- --run && npm run build
cd ../e2e && npx playwright test      # também grava docs/evidencias/itens-checklist-e2e.csv
git status --short && git log --oneline -5
```

**Critérios de aceite.** CA111–CA116 (seção 11 do handoff). O CSV por inspeção segue com as mesmas colunas.

**Evidências.** `docs/evidencias/R3-exportacao-itens.md` e o CSV de exemplo gerado pelo E2E.

**Condição de parada.** Parar se a exportação exigir mudar as colunas do CSV atual, se aparecer conflito no `git pull --rebase` ou se faltar credencial no push.
