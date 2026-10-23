# Especificação SDD — Inspeções Simuladas

> **Spec-Driven Development.** Este documento é a especificação viva do sistema: o que ele deve fazer, as regras que não podem ser quebradas, como cada requisito é verificado e como retomar o trabalho em uma nova sessão. **Todos os dados do sistema são fictícios** (nenhum dado real da SEMA/MT).

| Campo | Valor |
|---|---|
| Sistema | Inspeções Simuladas (laboratório SEMA/MT, fictício) |
| Estado desta especificação | 2026-10-23, rodadas M0 parcial, S0 a S3, R1, R2 e R3 entregues |
| Repositório | https://github.com/tiagobatista-stack/unidade_8_desafio_21 (branch `main`) |
| Frontend publicado | https://unidade-8-desafio-21.vercel.app (só funciona com o backend local do mesmo computador) |
| Verificação de referência | backend **348**, frontend **125**, E2E **14** passos, build ok |
| Fonte do texto completo das regras | `HANDOFF_CLAUDE_CODE.md` (RN01–RN47, CA01–CA116, P1–P17, PB1–PB3) |

## 0. Como usar este documento (laço SDD)

1. **Especificar primeiro.** Toda mudança de comportamento começa aqui e no `HANDOFF_CLAUDE_CODE.md` (regra nova = RN nova; critério novo = CA novo, **sem renumerar os antigos**).
2. **Critério antes do código.** Escreva o critério de aceite verificável e o teste que o cobre; só então implemente.
3. **Planejar e dividir.** `PLANO_EXECUTAVEL.md` guarda o plano por rodada (objetivo, prompt, verificação, parada).
4. **Verificar.** Rode backend, frontend, build e E2E. Todo número diferente de §12 precisa ser explicado. Nunca relaxar teste para passar.
5. **Registrar.** Atualize README, HANDOFF, evidências e esta especificação. Commits separados por assunto (§17).

Hierarquia de verdade, da mais forte para a mais fraca: **testes automatizados e código** (especificação executável) → `HANDOFF_CLAUDE_CODE.md` (texto normativo completo) → este documento (síntese e protocolo) → README (uso).

## 1. Visão

**Problema.** Simular o fluxo de uma inspeção ambiental de campo: cadastrar o empreendimento, abrir a inspeção, registrar o checklist e as fotografias com anotação, fechar com resultado calculado e emitir um relatório numerado, imprimível e imutável.

**Usuário.** Uma única pessoa, trabalhando em seu computador (papéis de desenho: *Inspetor simulado*, que faz tudo, e *Gestor*, que consulta; sem controle de acesso).

**Resultado esperado.** Uma ferramenta local, rastreável e testada, cujo relatório de uma inspeção finalizada **nunca muda**, mesmo que o cadastro do empreendimento seja editado depois.

## 2. Escopo

**Dentro:** locais (com CAR e proprietários), inspeções (número do processo, agendamento, edição por status, cancelamento, fechamento), checklist de 6 itens do modelo mais itens avulsos, observações da vistoria, fotos com anotação obrigatória, painel com 3 indicadores, listas filtráveis, duas exportações CSV, carga de dados de exemplo, relatório numerado com prévia e impressão A4, migração leve do banco.

**Fora (decisões vigentes):** login e permissões reais, múltiplos usuários, nuvem e sincronização, app móvel, edição do modelo de checklist, inativação ou exclusão de locais, reabertura de inspeção finalizada, histórico e auditoria, geração de PDF no servidor, mapa e geolocalização, edição de imagens, busca textual além do filtro por número do processo, backup automático, integração com sistemas reais. Lista completa na seção 13 do HANDOFF.

## 3. Princípios invariantes

Violar qualquer um exige decisão explícita do usuário e atualização desta seção.

| Id | Princípio |
|---|---|
| PRI-01 | **Regras de negócio só no backend** (`routers → services → repositories`, com `domain` de funções puras). A interface exibe, valida só presença/sintaxe e repassa erros. O que a tela pode ou não fazer vem da API (`campos_editaveis`, `fechamento_bloqueado_motivo`, `registro_bloqueado_motivo`). |
| PRI-02 | **Sem login; API só em `127.0.0.1`.** O frontend na Vercel chama a API local pelo navegador (CORS só para as origens de `CORS_ORIGINS`). |
| PRI-03 | **Dados 100% fictícios** no seed, nos testes e nas capturas (proprietários "… Fictício", telefones `(65) 90000-000N`, CAR `MT-5107925-0000…`). Nome e telefone reais são dados pessoais (LGPD): nunca entram no repositório. |
| PRI-04 | **Relógio injetável** (`clock.py`; `INSPECOES_HOJE`). Nos testes "hoje" é 2026-10-23. |
| PRI-05 | **Inspeção FINALIZADA ou CANCELADA é imutável** (inspeção, itens, observações e fotos). O relatório e o empreendimento da finalizada vêm da **cópia gravada no fechamento**. |
| PRI-06 | **Texto livre é texto puro**: escapado na tela (quebras preservadas) e protegido contra fórmulas nos CSV. |
| PRI-07 | **Validar antes de gravar**; gravar arquivo antes do registro e compensar em falha; fechamento é **atômico** (resultado, status, cópia e número no mesmo commit). |
| PRI-08 | **Migração sem Alembic**, leve e **idempotente**, na subida da API (`_garantir_colunas` e `preencher_legado`), sem perder dados. |
| PRI-09 | **Sem biblioteca de PDF no backend.** O relatório é impresso pelo navegador (`@media print`, A4). |
| PRI-10 | **CAR é texto livre**: nenhum formato (SICAR, SIMCAR-MT ou outro) é rejeitado sem confirmação do usuário. |
| PRI-11 | **Não relaxar testes.** Corrigir a causa. Número de testes diferente do esperado precisa de explicação. |
| PRI-12 | Identificadores de código em português sem acento; mensagens ao usuário em português; commits Conventional Commits em português. |

## 4. Glossário

| Termo | Significado |
|---|---|
| Local / empreendimento | Cadastro do lugar vistoriado (nome, município, tipo, coordenadas em MT, CAR, proprietários) |
| Inspeção | Vistoria agendada (`INS-NNN`), com número de processo, checklist, observações e fotos |
| Modelo de checklist | 6 itens fixos (3 críticos) copiados para cada inspeção nova |
| Item avulso | Item acrescentado a uma única inspeção |
| Cópia do empreendimento | JSON gravado ao fechar, com os dados do Local daquele momento |
| Relatório | Documento numerado `NNNN/AAAA` (finalizada) ou prévia sem número (demais status) |
| Prévia | Relatório de inspeção não finalizada, marcado "PRÉVIA, NÃO FINALIZADO" |
| Legado | Dados criados antes de um campo existir; preenchidos na subida da API |

## 5. Modelo de domínio

Banco SQLite (`backend/data/inspecoes.db`), SQLAlchemy, constraints portáveis (`PRAGMA foreign_keys=ON`). Fotos em `backend/data/fotos/{inspecao_id}/original|miniatura/{uuid}.ext`.

| Entidade | Campos e invariantes |
|---|---|
| `local` | `nome` único ≤120; `municipio` ≤80; `tipo` ≤40; `latitude` -18,05..-7,35 e `longitude` -61,65..-50,20 (CHECK); `ativo`; `numero_car` ≤60 opcional, maiúsculas |
| `proprietario` | `local_id` FK CASCADE; `nome` ≤120 obrigatório; `telefone` só dígitos, 10 ou 11 (CHECK), opcional; `ordem`; máx. 20 por local |
| `modelo_item` | `descricao`, `critico`, `ativo`, `ordem`; 6 itens criados na inicialização |
| `inspecao` | `codigo` único `INS-NNN`; `numero_processo` ≤60 (obrigatório na API, nulo só em legado); `local_id` FK; `objetivo` ≤200; `observacoes` ≤2000; `observacoes_vistoria` ≤2000; `data_agendamento`; `data_realizacao` ≥ agendamento; `status`; `resultado` só se FINALIZADA; `motivo_cancelamento` ≤300 obrigatório se CANCELADA; `fechado_em` só se FINALIZADA; `empreendimento_json` (cópia); `numero_relatorio` `NNNN/AAAA` com índice único |
| `item_inspecao` | `inspecao_id` FK CASCADE; `modelo_item_id` (só origem MODELO); `descricao` ≤200; `critico`; `situacao` (NAO_RESPONDIDO, CONFORME, NAO_CONFORME, NAO_SE_APLICA); `observacao` ≤1000; `origem` (MODELO, AVULSO); `ordem` |
| `foto_vistoria` | `inspecao_id` FK CASCADE; `item_inspecao_id` FK SET NULL; `arquivo_path` único; `mime_type` jpeg/png/webp; `tamanho_bytes` 1..5.242.880; `hash_sha256` único por inspeção; `legenda` ≤200; `anotacao` 1..1000 (obrigatória); `data_captura`; `ordem` |
| `contador_relatorio` | `ano` PK; `ultimo`: último número emitido no ano; nunca decresce |

Relacionamentos: Local 1—N Inspeção; Local 1—N Proprietário; Inspeção 1—N Item; Inspeção 1—N Foto; Item 0..1—N Foto.

## 6. Ciclo de vida da inspeção

```
ABERTA ──(1º item com situação ≠ NÃO RESPONDIDO)──▶ EM_ANDAMENTO ──(fechar)──▶ FINALIZADA
   └──(cancelar, com motivo)──▶ CANCELADA
```

| Status | Edição permitida | Ações |
|---|---|---|
| ABERTA | processo, local, agendamento, objetivo, observações, observações da vistoria; itens, avulsos e fotos | iniciar (registrar situação), cancelar. **Não fecha.** |
| EM_ANDAMENTO | processo, data de realização, observações, observações da vistoria; itens, avulsos e fotos | fechar |
| FINALIZADA, CANCELADA | nada (somente leitura) | gerar relatório (prévia se cancelada) |

**Fechamento** exige todos os itens respondidos e observação nos itens NÃO CONFORMES. Resultado: algum item **crítico** NÃO CONFORME → REPROVADA; senão algum NÃO CONFORME → APROVADA_COM_RESSALVAS; senão APROVADA.

**Início bloqueado por data:** registrar o 1º item de inspeção agendada para depois de hoje retorna 422 `DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO` (decisão P1/PB1: mantida; a tela avisa antes da tentativa).

## 7. Requisitos funcionais (formato EARS)

Referências: RN e CA no HANDOFF; testes em §16.

### 7.1 Locais e empreendimento
- **RF-01** O sistema deve permitir listar, cadastrar e editar locais (tela *Locais* e modal em *Nova inspeção*). *RN11, RN36, RN40; CA25–CA27, CA83, CA94.*
- **RF-02** Quando o CAR for informado, o sistema deve guardá-lo em maiúsculas, sem espaços nas pontas, até 60 caracteres, **sem rejeitar nenhum formato**. *RN39; CA91.*
- **RF-03** Quando um proprietário for informado, o sistema deve exigir o nome (≤120), aceitar telefone opcional com 10 ou 11 dígitos e DDD 11–99, guardá-lo só com dígitos, exibi-lo como `(65) 99999-9999`, apontar a linha do erro e limitar a 20 proprietários. *RN40; CA92.*
- **RF-04** Quando um local for atualizado (PUT), o sistema deve **substituir** a lista de proprietários pela enviada; um PUT inválido não altera nada. *CA93.*

### 7.2 Inspeção
- **RF-05** O sistema deve cadastrar a inspeção em ABERTA, com código sequencial `INS-NNN` nunca reutilizado e cópia dos 6 itens do modelo. Exige `numero_processo`, local ativo, `data_agendamento` e objetivo. *RN01, RN03, RN09, RN35; CA01–CA04, CA29, CA30, CA74, CA75.*
- **RF-06** O sistema deve editar a inspeção só nos campos do seu status e informar `campos_editaveis` na API; fora disso devolve 409. *RN14, RN38; CA33, CA76, CA77, CA81, CA82.*
- **RF-07** Quando a data de realização for informada, o sistema deve recusá-la se futura (422 `DATA_REALIZACAO_FUTURA`) ou anterior ao agendamento (422 `DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO`). *RN02, RN13; CA03, CA32.*
- **RF-08** O sistema deve cancelar só inspeção ABERTA, exigindo motivo. *RN08, RN15; CA20.*

### 7.3 Checklist, observações e fotos
- **RF-09** Quando a primeira situação diferente de NÃO RESPONDIDO for registrada em inspeção ABERTA, o sistema deve passar a inspeção para EM_ANDAMENTO e preencher a realização com hoje; salvar só observação **não** inicia. *CA05, CA06, CA31, CA87.*
- **RF-10** O sistema deve adicionar e remover itens avulsos (nunca remover itens do modelo) e permitir voltar um item para NÃO RESPONDIDO enquanto a inspeção não for terminal. *RN09; CA07, CA08.*
- **RF-11** O sistema deve aceitar observações da vistoria de até 2000 caracteres (espaços viram vazio) em ABERTA e EM_ANDAMENTO. *RN16–RN19; CA35–CA41.*
- **RF-12** Quando uma foto for enviada, o sistema deve validar o tipo **pelo conteúdo**, limitar a 5 MB e 20 por inspeção, recusar duplicata (hash), exigir anotação de 1 a 1000 caracteres, remover EXIF/GPS, gerar miniatura de 320 px e vincular opcionalmente a um item da mesma inspeção. A ordem de validação é: estado (409) → campos e arquivo (422/413/415) → limite e duplicidade (409) → gravar. *RN20–RN34; CA42–CA73.*

### 7.4 Fechamento, cópia e relatório
- **RF-13** Quando o usuário fechar uma inspeção EM_ANDAMENTO completa, o sistema deve, **na mesma transação**, copiar os dados do empreendimento, reservar o número do relatório, calcular o resultado e finalizar. Falha em qualquer passo desfaz tudo. *RN04–RN06, RN41, RN42; CA09–CA14, CA96, CA97.*
- **RF-14** Fechar inspeção ABERTA deve devolver 409 `TRANSICAO_INVALIDA` com orientação clara; o detalhe deve informar o motivo antes da tentativa. *RN45; CA86.*
- **RF-15** O número do relatório deve ser `NNNN/AAAA`, sequencial por ano (relógio injetável), único e nunca reutilizado; cancelar, fechamento bloqueado e prévia não consomem número. *RN42; CA99–CA101.*
- **RF-16** O relatório deve conter, nesta ordem: 1 Identificação, 2 Empreendimento, 3 Objetivo e observações, 4 Checklist (numerado, com totais e críticos não conformes destacados), 5 Registro fotográfico (imagem original, no máximo 2 por página), 6 Conclusão (resultado e regra aplicada). *RN43; CA102–CA104.*
- **RF-17** Inspeção não finalizada deve gerar **prévia** sem número, com a marca "PRÉVIA, NÃO FINALIZADO" ("CANCELADA, NÃO FINALIZADO" se cancelada), usando os dados atuais do local. *CA105.*
- **RF-18** O sistema deve oferecer impressão A4 pelo navegador, sem menu nem botões, com rodapé e "Página X de Y" em todas as páginas, e só liberar o botão após as imagens carregarem. *RN44; CA106, CA107.*

### 7.5 Aviso, painel, listas e exportações
- **RF-19** A tela deve avisar que só registrar a situação inicia a inspeção, e, quando o agendamento for futuro, avisar **antes** da tentativa, com link para editar, desabilitando os seletores de situação (a API continua bloqueando). *RN45; CA87, CA88.*
- **RF-20** O painel deve mostrar Inspeções (exclui canceladas), Pendências (ABERTA + EM_ANDAMENTO) e Finalizadas, clicáveis para a lista da categoria; invariante Pendências + Finalizadas = Inspeções. *RN37; CA18–CA21, CA80.*
- **RF-21** A lista deve filtrar por status (inclusive vários), período (sobre o agendamento) e trecho do número do processo, mostrar o filtro ativo e o botão Editar só em status editável. *CA15, CA16, CA78, CA79, CA81.*
- **RF-22** O sistema deve exportar dois CSV (`;`, UTF-8 com BOM, texto protegido contra fórmulas): por inspeção e **por item do checklist**, sem que um altere o outro. *RN47; CA23, CA28, CA85, CA111–CA116.*
- **RF-23** O sistema deve carregar dados de exemplo (4 locais, 5 inspeções, 9 fotos) só em banco sem locais nem inspeções (409 `BANCO_JA_POVOADO`), esperando o painel 5 / 2 / 3. *CA18, CA24.*

### 7.6 Migração
- **RF-24** Na subida da API o sistema deve acrescentar colunas e tabelas novas e preencher o legado (cópia e número das finalizadas antigas), de forma idempotente, sem perder dados. *PRI-08; CA84, CA98, CA109.*

## 8. Requisitos não funcionais

| Id | Requisito | Verificação |
|---|---|---|
| RNF-01 | **Privacidade/LGPD:** só dados fictícios no repositório; dados reais ficam em `backend/data/` (ignorado pelo Git, inclusive `backend/data_backup*/`). | revisão antes de cada commit; `test_seed_so_tem_dados_ficticios` |
| RNF-02 | **Segurança:** texto puro escapado; nome de arquivo nunca compõe caminho; tipo de imagem por conteúdo; CORS só para origens listadas; erro 500 sem detalhes técnicos. | `test_api_fotos`, `test_cors`, `test_erro_interno_nao_vaza_detalhes` |
| RNF-03 | **Portabilidade para PostgreSQL:** tipos e constraints portáveis; consulta de indicadores única e condicional. | revisão; caminho documentado no README |
| RNF-04 | **Acessibilidade de formulário:** todo campo com `id`, `name` e `label` associado. | `correcoes-a.test.tsx` (verificação genérica) |
| RNF-05 | **Impressão:** A4, rodapé e numeração por caixas de margem do `@page`; sem `position: fixed` para rodapé. | `relatorio.test.tsx`; PDFs gerados no E2E |
| RNF-06 | **Limites:** foto ≤5.242.880 B e ≤20 por inspeção; lista de inspeções até 100 por consulta (`tamanho` ≤100). | testes de API |
| RNF-07 | **Consistência arquivo × registro** com utilitário de verificação. | `test_verificar_fotos_*` |
| RNF-08 | **Reprodutibilidade:** testes com relógio fixo, banco em memória e imagens geradas por código. | suítes |

## 9. Contrato de API (`/api/v1`)

| Método e caminho | Função |
|---|---|
| GET `/health` | vida |
| GET/POST `/locais`, GET/PUT `/locais/{id}` | locais com `numero_car` e `proprietarios[{nome, telefone}]` (resposta traz também `telefone_formatado`) |
| POST/GET `/inspecoes` | cadastrar (exige `numero_processo`) / listar com filtros `status` (repetível), `numero_processo`, `data_inicio`, `data_fim`, `local_id`, `pagina`, `tamanho` |
| GET/PATCH `/inspecoes/{id}` | detalhe (itens, fotos, `empreendimento`, `campos_editaveis`, `fechamento_bloqueado_motivo`, `registro_bloqueado_motivo`, `numero_relatorio`) / edição por status |
| POST `/inspecoes/{id}/cancelar`, `/fechar` | transições |
| GET `/inspecoes/{id}/relatorio` | relatório estruturado (prévia ou numerado) |
| GET/POST `/inspecoes/{id}/itens`, PATCH/DELETE `/inspecoes/{id}/itens/{item_id}` | checklist |
| POST/GET `/inspecoes/{id}/fotos`, GET/PATCH/DELETE `/inspecoes/{id}/fotos/{foto_id}`, GET `…/arquivo?versao=miniatura\|original` | fotos |
| GET `/indicadores` | `{inspecoes, pendencias, finalizadas, gerado_em}` |
| GET `/exportacao/inspecoes.csv`, `/exportacao/itens.csv` | CSV |
| POST `/utilitarios/carregar-exemplos`, GET `/utilitarios/verificar-fotos` | utilitários |

**Contrato de erro único:** `{"erro": {"codigo", "mensagem", "detalhes": [{"campo", "mensagem"}]}}`.

| HTTP | Códigos |
|---|---|
| 422 | `VALIDACAO_CAMPO`, `DATA_REALIZACAO_FUTURA`, `DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO`, `COORDENADA_FORA_DE_MT`, `FECHAMENTO_BLOQUEADO`, `ITEM_NAO_PERTENCE_A_INSPECAO` |
| 409 | `TRANSICAO_INVALIDA`, `INSPECAO_IMUTAVEL`, `CAMPO_NAO_EDITAVEL_NO_STATUS`, `ITEM_DE_MODELO_NAO_REMOVIVEL`, `LIMITE_FOTOS_EXCEDIDO`, `FOTO_DUPLICADA`, `BANCO_JA_POVOADO` |
| 413 / 415 | `FOTO_TAMANHO_EXCEDIDO` / `FOTO_FORMATO_INVALIDO` |
| 404 | `NAO_ENCONTRADO`, `FOTO_ARQUIVO_AUSENTE` |
| 500 | `ERRO_INTERNO` |

## 10. Interface

| Rota | Tela e comportamento essencial |
|---|---|
| `/` | Painel: 3 cartões clicáveis, atalhos, Carregar exemplos, Exportar CSV, Exportar itens (CSV) |
| `/inspecoes` | Lista: colunas com processo, filtros (status, grupos, período, processo), Editar só em status editável |
| `/inspecoes/nova` | Nova inspeção: processo, local (com lat/long), **+ Novo local**, agendamento, objetivo, observações |
| `/inspecoes/:id` | Detalhe: empreendimento, avisos orientativos, checklist, observações, fotos, Fechar/Cancelar, Gerar relatório |
| `/inspecoes/:id/editar` | Edição só dos campos de `campos_editaveis` |
| `/inspecoes/:id/relatorio` | Relatório numerado ou prévia; Imprimir / Salvar PDF |
| `/locais`, `/locais/novo`, `/locais/:id/editar` | Locais com CAR e proprietários (adicionar/remover) |

Todas as telas tratam carregando, vazio e erro (mensagem e detalhes da API).

## 11. Critérios de aceite

Texto normativo de cada critério: seção 11 do HANDOFF. A numeração é **estável** (não renumerar).

| Faixa | Assunto | Onde é verificado |
|---|---|---|
| CA01–CA34 | cadastro, itens, fechamento, consulta, datas | `test_inspecao_service`, `test_api_inspecoes`, `test_dominio`, `test_persistencia` |
| CA18–CA28, CA58 | painel, exemplos, CSV por inspeção | `test_api_painel` |
| CA35–CA41 | observações da vistoria | serviço e API; `fotos.test.tsx` |
| CA42–CA73 | fotos e anotações | `test_api_fotos`, `test_imagem_storage`, `test_persistencia_fotos`, `fotos.test.tsx` |
| CA74–CA85 | R1: processo, editar, cartões, novo local, migração, CSV | `test_numero_processo`, `test_migracao`, `novas-funcoes.test.tsx` |
| CA86–CA110 | R2: usabilidade, CAR e proprietários, cópia, numeração, relatório | `test_orientacoes`, `test_locais_empreendimento`, `test_copia_fechamento`, `test_relatorio`, `locais.test.tsx`, `correcoes-a.test.tsx`, `relatorio.test.tsx` |
| CA111–CA116 | R3: exportação dos itens | `test_exportacao_itens`, `paginas.test.tsx` |

## 12. Estratégia de verificação

```
cd backend  && pytest -q                    # 348 testes
cd frontend && npm test -- --run            # 125 testes
cd frontend && npm run build                # tsc + vite
cd e2e      && npx playwright test          # 14 passos; regrava telas, PDFs do relatório e CSVs de exemplo
```

| Backend (por arquivo) | Testes | Frontend (por arquivo) | Testes |
|---|---|---|---|
| api/test_api_fotos | 36 | tests/paginas | 24 |
| api/test_api_inspecoes | 36 | tests/fotos | 14 |
| api/test_api_painel | 14 | tests/novas-funcoes | 22 |
| api/test_banco_novo | 3 | tests/correcoes-a | 19 |
| api/test_copia_fechamento | 9 | tests/locais | 16 |
| api/test_cors | 2 | tests/relatorio | 30 |
| api/test_exportacao_itens | 14 | **Total** | **125** |
| api/test_health | 2 | | |
| api/test_locais_empreendimento | 16 | | |
| api/test_numero_processo | 25 | | |
| api/test_orientacoes | 11 | | |
| api/test_relatorio | 21 | | |
| service/test_inspecao_service | 38 | | |
| unit/test_clock | 3 | | |
| unit/test_contato | 25 | | |
| unit/test_dominio | 24 | | |
| unit/test_dominio_relatorio | 8 | | |
| unit/test_fotos_exemplo | 5 | | |
| unit/test_imagem_storage | 15 | | |
| unit/test_legado_copia | 8 | | |
| unit/test_migracao | 5 | | |
| unit/test_persistencia | 18 | | |
| unit/test_persistencia_fotos | 10 | | |
| **Total** | **348** | | |

**E2E (Playwright, Chromium, API e Vite próprios, banco temporário, data fixa 2026-10-23):** painel vazio e exemplos 5/2/3; lista e filtros; contadores clicáveis; editar e busca por processo; Locais com CAR e proprietários; nova inspeção e cancelamento; aviso de agendamento futuro; fechamento bloqueado; fotos e falha parcial; fechar (1 pendência, 4 finalizadas); cópia no fechamento; relatório e PDF; inspeção reprovada em tela estreita; CSV (inclusive itens) e verificação de fotos.

**Evidências:** `docs/evidencias/` (S1A, S1B, S2-S3-E2E, R1, R2, R3, telas, PDFs do relatório, CSVs de exemplo). Os PDFs foram **conferidos página a página** (rodapé, "Página X de Y", no máximo 2 fotos por página, marca da prévia em todas as páginas).

**Boas práticas de verificação aprendidas:** testar o comportamento real quando o DOM não basta (o PDF revelou rodapé cobrindo conteúdo); fazer "teste de mutação" manual em testes novos (quebrar o código e ver o teste falhar); olhar as capturas de tela.

## 13. Decisões (ADR resumido)

| Id | Decisão | Motivo | Consequência |
|---|---|---|---|
| ADR-01 | FastAPI + SQLAlchemy + SQLite em arquivo; React + Vite + TypeScript | simplicidade local, um usuário | PostgreSQL exigiria `DATABASE_URL`, Alembic e fotos em armazenamento de objetos |
| ADR-02 | Metadados de foto no banco, arquivos em disco por interface `storage` | simplicidade e backup manual | backup = `.db` + `fotos/` |
| ADR-03 | Relógio injetável | testes determinísticos | `INSPECOES_HOJE` no E2E |
| ADR-04 | Migração leve e idempotente no lugar de Alembic | banco local sem ferramenta extra | cada coluna nova entra em `_garantir_colunas`, com teste de banco antigo |
| ADR-05 | Cópia JSON do empreendimento no fechamento | relatório imutável | lista e CSV mostram o local atual, não a cópia |
| ADR-06 | Número do relatório por contador anual + índice único | sem repetição, nem na virada de ano | número só na finalizada |
| ADR-07 | Relatório impresso pelo navegador, rodapé e numeração em `@page` | sem dependência de PDF no backend | "Página X de Y" conferida só no Chromium |
| ADR-08 | Backend monta o relatório e as orientações; a tela só exibe | regras no backend (PRI-01) | contrato da API cresce (`campos_editaveis`, motivos) |
| ADR-09 | Vistoria antes do agendamento fica **bloqueada** com aviso preventivo (PB1a) | mantém o CHECK de datas | opção (c) descartada; (b) não escolhida |
| ADR-10 | Frontend na Vercel com backend local (`VITE_API_URL=http://127.0.0.1:8000`) | combinado com o usuário | só funciona no computador do backend; navegador pede permissão de rede local |
| ADR-11 | CSV dos itens como arquivo separado | não quebrar o CSV atual | duas exportações no painel |

## 14. Estado atual e backlog

**Entregue:** S0 estrutura; S1A e S1B API; S2A e S2B frontend; S3 painel, exemplos e CSV; R1 melhorias pós-uso; R2 usabilidade, empreendimento, cópia e relatório; R3 exportação dos itens. Frontend publicado.

**Pendências abertas**

| Item | Situação |
|---|---|
| M0 — documentos formais (`requisitos.md`, `criterios-aceite.md`, ADRs, `migracao-postgresql.md`) | não escritos; este SDD e o HANDOFF cobrem requisitos e critérios, mas não substituem as ADRs formais |
| Matriz CA01–CA116 completa (S4) | parcial: o mapeamento por rodada está em `docs/evidencias/*.md` e §11/§16 |
| P10 licença e visibilidade do repositório | indefinidas (decisão do dono do produto) |
| PB2 `respondido_em` por item | **adiado** por decisão do usuário (exigiria ADD COLUMN) |

**Backlog sugerido (não decidido)**

- paginação na tela de inspeções (hoje até 100 por consulta);
- inativar ou excluir locais;
- lista e CSV usando a cópia do empreendimento nas finalizadas;
- E2E no CI e em outros navegadores (Firefox, WebKit); conferir "Página X de Y" fora do Chromium;
- teste com fechamentos realmente simultâneos;
- auditoria completa de acessibilidade;
- hospedar o backend em nuvem (PostgreSQL e armazenamento de objetos) para o site da Vercel funcionar fora do computador do usuário.

**Limitações conhecidas:** uso local de um usuário; cópia do empreendimento das finalizadas antigas reflete o Local de hoje; CAR e telefones validados só quanto a tamanho e DDD; "Página X de Y" verificada só no Chromium.

## 15. Operação

```
# backend/ (venv ativo)
pip install -e ".[dev]"
uvicorn app.main:app --host 127.0.0.1 --port 8000
# frontend/
npm install && npm run dev                      # http://localhost:5173
```

| Variável | Efeito |
|---|---|
| `DATABASE_URL`, `FOTOS_DIR` | banco e fotos (padrão em `backend/data/`) |
| `CORS_ORIGINS` | origens externas liberadas (sem ela, nenhuma) |
| `INSPECOES_HOJE` | fixa "hoje" (AAAA-MM-DD) |
| `API_URL` (Vite dev), `VITE_API_URL` (build) | destino do proxy e endereço da API embutido |

**Atualizar banco existente:** parar a API, copiar `backend/data/` (o `.db` e `fotos/`), atualizar o código e subir a API; a migração é automática. Para recomeçar do zero, apagar `backend/data/` (**apaga todos os dados**).

**Vercel:** projeto `unidade-8-desafio-21` (equipe `tiago-alexandre`), raiz `frontend`, preset Vite. **Cada push em `main` gera deploy de produção** (conferido; a opção `createDeployments` aparece como `disabled` na API, mas não vale na prática). Deploy manual: `vercel deploy --prod` a partir da **raiz** do repositório. O token da Vercel fica em `.env.local` (ignorado pelo Git).

**Armadilhas conhecidas**

- Fechamento: reservar cópia e número **antes** de alterar resultado e status (autoflush consulta o banco e o CHECK recusa estado pela metade).
- Impressão: nada de `position: fixed` para rodapé; usar caixas de margem do `@page`.
- Git: usar `git add` **explícito**, nunca `-A` (há `.env.local`, `backend/data_backup*/` e arquivos gerados). O E2E regrava telas e PDFs com horário; commitar só o que mudou de verdade.
- Windows: o navegador pede permissão de rede local para o site da Vercel chamar `127.0.0.1`; sem ela o painel mostra "Não foi possível conectar à API."
- Após atualizar o código, reiniciar a API em execução.

## 16. Rastreabilidade (requisito → regra → critério → verificação)

| Requisito | Regras | Critérios | Testes principais |
|---|---|---|---|
| RF-01 a RF-04 locais e empreendimento | RN11, RN36, RN39, RN40 | CA25–CA27, CA83, CA91–CA95 | `test_locais_empreendimento`, `test_contato`, `locais.test.tsx`, passo E2E "Locais" |
| RF-05 a RF-08 inspeção | RN01–RN03, RN08, RN13–RN15, RN35, RN38 | CA01–CA04, CA20, CA29–CA34, CA74–CA77, CA81, CA82 | `test_api_inspecoes`, `test_numero_processo`, `test_inspecao_service`, `novas-funcoes.test.tsx` |
| RF-09 a RF-12 checklist, observações, fotos | RN09, RN16–RN34 | CA05–CA08, CA35–CA73 | `test_api_fotos`, `test_imagem_storage`, `fotos.test.tsx` |
| RF-13 a RF-15 fechamento, cópia, número | RN04–RN06, RN41, RN42, RN45 | CA09–CA14, CA86, CA96–CA101 | `test_copia_fechamento`, `test_relatorio`, `test_orientacoes`, `test_legado_copia` |
| RF-16 a RF-18 relatório e impressão | RN43, RN44 | CA102–CA107 | `test_relatorio`, `test_dominio_relatorio`, `relatorio.test.tsx`, PDFs do E2E |
| RF-19 avisos | RN45 | CA87, CA88 | `test_orientacoes`, `correcoes-a.test.tsx` |
| RF-20 e RF-21 painel e lista | RN37 | CA15–CA21, CA78–CA80 | `test_api_painel`, `test_numero_processo`, `novas-funcoes.test.tsx` |
| RF-22 e RF-23 exportações e exemplos | RN47 | CA18, CA23, CA24, CA28, CA85, CA111–CA116 | `test_api_painel`, `test_exportacao_itens`, E2E |
| RF-24 migração | PRI-08 | CA84, CA98, CA109 | `test_migracao`, `test_legado_copia` |
| RNF-04 acessibilidade de formulário | RN46 | CA89 | `correcoes-a.test.tsx` |

## 17. Protocolo de mudança e de commits

1. Escrever/ajustar a regra (RN) e o critério (CA novo, número seguinte) no HANDOFF e aqui.
2. Escrever o teste que falha; implementar; fazer o teste passar.
3. Rodar backend, frontend, build e E2E; explicar toda diferença de contagem.
4. Conferir arquivos antes do commit (nenhum `.env*`, `backend/data*`, `dist`, `node_modules`, `.venv`, `test-results`, `.db`, fotos reais) e dados só fictícios.
5. Commits separados por assunto, mensagens em português com prefixo `feat:`, `fix:`, `docs:`, `test:` ou `chore:`.
6. `git fetch`; se `origin/main` avançou, `git pull --rebase` (conflito: parar e mostrar); `git push origin main`, **nunca `--force`**; falha de credencial: informar o erro, sem gravar token.
7. Conferir o deploy na Vercel (cada push gera um) e o `git status` limpo.

## 18. Retomada e encerramento de sessão

**Checklist de encerramento (estado em 2026-10-23)**

- [x] `main` publicado no GitHub, `git status` limpo
- [x] backend 348, frontend 125, E2E 14 verdes; build ok
- [x] README, HANDOFF, PLANO, CLAUDE.md e evidências atualizados
- [x] deploy da Vercel `READY` a cada push
- [ ] decisões do dono do produto: licença (P10); rever `respondido_em` (PB2) quando quiser
- [ ] documentos formais do M0 (opcional)

**Prompt de retomada (colar no início da próxima sessão)**

```
Leia docs/SPEC_SDD.md, HANDOFF_CLAUDE_CODE.md (RN, CA, P, PB) e CLAUDE.md.
Estado: MVP completo com rodadas R1, R2 e R3; backend 348, frontend 125, E2E 14 verdes.
Regras: siga o laço SDD (especificar -> critério -> teste -> código -> docs), não relaxe testes,
use dados só fictícios, use git add explícito, commits em português por assunto, push sem --force.
Antes de mexer, rode as quatro verificações da seção 12 e confirme os números.
Pendências: P10 (licença), PB2 (respondido_em, adiado), M0 formal, backlog da seção 14.
Pergunte ao usuário antes de: rejeitar formatos de CAR, adicionar dependência de PDF no backend,
alterar a regra de vistoria antes do agendamento ou publicar dados reais.
```
