# HANDOFF_CLAUDE_CODE.md — Inspeções Simuladas (laboratório SEMA/MT, fictício)

> Fonte única de verdade do escopo aprovado. Use como base do `/init` (CLAUDE.md) e do `README.md`.
> Todos os dados são **fictícios**. Nenhum dado real da SEMA/MT.
> Data de referência da consolidação: 23/10/2026. **Atualizado em 23/10/2026** após a rodada de melhorias pós-uso (seção 16) e a rodada R2 (CAR e proprietários, cópia no fechamento, relatório numerado).

## 0. Regras de trabalho (leia antes de qualquer ação)

1. **Uma sprint por vez.** Execute somente a sprint pedida no prompt. Ao cumprir os critérios de aceite, **pare** e relate evidências. Não avance sozinho.
2. **Não reinvente o escopo.** O que não está neste arquivo está fora do escopo. Dúvida de regra: consulte a seção 9 (Pendências); se não estiver lá, pergunte antes de decidir.
3. **Regras de negócio só na camada de serviço/domínio** (backend). O front exibe e repassa erros.
4. **Sem login no MVP.** API escuta somente em `127.0.0.1`.
5. **Relógio injetável** (`clock.py`): "hoje" nos testes é fixo em **2026-10-23**.
6. **Sem dados reais** e sem imagens reais. Imagens de exemplo são geradas por programa.
7. Cada sprint termina com: testes verdes, commit(s) no padrão Conventional Commits, atualização da seção 10 (status) deste arquivo.
8. Idioma: documentação e mensagens ao usuário em português; identificadores de código em português sem acento (ex.: `data_agendamento`) para espelhar o domínio.
9. Quando uma verificação falhar, **corrija a causa**; não enfraqueça o teste nem pule critérios. Se não conseguir, pare e reporte.

## 1. Produto

Ferramenta **local, para um único usuário**, que permite: cadastrar uma inspeção (com data de agendamento), registrar os itens do checklist, anotar o contexto e fotografias da vistoria, e fechar a inspeção com resultado calculado. Painel com 3 indicadores: **Inspeções, Pendências, Finalizadas**.

Perfis (apenas papéis de desenho, sem controle de acesso): *Inspetor simulado* (tudo) e *Gestor* (leitura/indicadores).

## 2. Stack e decisões arquiteturais

- **Backend:** Python + FastAPI, SQLAlchemy, SQLite em arquivo (`backend/data/inspecoes.db`), `DATABASE_URL` configurável. pytest. Pillow e python-multipart (fotos).
- **Frontend:** React + Vite + TypeScript, TanStack Query, Vitest + Testing Library. Proxy `/api` → `127.0.0.1:8000`.
- **Camadas:** `routers → services → repositories`; `domain` com funções puras.
- **Prefixo da API:** `/api/v1`. Datas em ISO (`2026-10-20`); a interface exibe `dd/mm/aaaa`.
- **ADR-001 (aceita):** arquitetura acima; sem autenticação no MVP (ponto único de dependência de segurança, vazio, para plugar login depois); SQLite agora, PostgreSQL depois sem reescrita (apenas tipos/constraints portáveis, `PRAGMA foreign_keys=ON`); sem DELETE de inspeção (cancelamento com motivo); Alembic só na migração.
- **ADR-002 (aceita):** metadados de foto no banco, **arquivos em disco** (`backend/data/fotos/{inspecao_id}/original|miniatura/{uuid}.ext`) via interface `storage`; miniatura (lado maior 320 px); EXIF removido; arquivos servidos só pela API; backup = `.db` **+** pasta `fotos/`.
- **Caminho PostgreSQL:** definir `DATABASE_URL`, adotar Alembic, revisar CHECKs, rodar suíte de API em PG no CI. Documentar em `docs/migracao-postgresql.md`.

## 3. Entidades e campos

**Local:** id; nome (único, ≤120); municipio (≤80); tipo (≤40); latitude decimal(8,5) CHECK −18,05..−7,35; longitude decimal(8,5) CHECK −61,65..−50,20; ativo (padrão verdadeiro). **numero_car** (texto livre ≤60, opcional, guardado em maiúsculas; nenhum formato é rejeitado); **proprietarios** 0..20 em tabela própria `proprietario` (id; local_id FK CASCADE; nome ≤120 obrigatório; telefone só dígitos, 10 ou 11 com DDD, opcional; ordem).

**Inspecao:** id; codigo (único, `INS-` + id 3 dígitos, gerado); **numero_processo** (texto livre ≤60, obrigatório no cadastro e na edição; nulo apenas em linhas criadas antes do campo existir; não único; ex.: `SEMA-PRO-2026/12345`); local_id FK; objetivo (≤200, obrig.); observacoes (texto, opc.); **observacoes_vistoria** (texto ≤2000, opc.); data_agendamento (obrig.); data_realizacao (opc., CHECK ≥ agendamento); status (`ABERTA`,`EM_ANDAMENTO`,`FINALIZADA`,`CANCELADA`); resultado (`APROVADA`,`APROVADA_COM_RESSALVAS`,`REPROVADA`; só se FINALIZADA); motivo_cancelamento (≤300; obrig. se CANCELADA); criado_em; atualizado_em; fechado_em (só FINALIZADA). **empreendimento_json** (Text; cópia JSON dos dados do empreendimento gravada no fechamento); **numero_relatorio** (`NNNN/AAAA`, único, só em FINALIZADA). Tabela auxiliar `contador_relatorio` (ano PK; ultimo): último número emitido em cada ano, nunca decresce.

**ItemInspecao:** id; inspecao_id FK (CASCADE); modelo_item_id FK opc.; descricao (≤200); critico; situacao (`NAO_RESPONDIDO` padrão,`CONFORME`,`NAO_CONFORME`,`NAO_SE_APLICA`); observacao; origem (`MODELO`,`AVULSO`); ordem.

**ModeloItem:** id; descricao; critico; ativo; ordem.

**FotoVistoria:** id; inspecao_id FK (CASCADE); item_inspecao_id FK opc. (SET NULL); nome_original (≤200); arquivo_path (único); miniatura_path; mime_type (`image/jpeg|png|webp`); tamanho_bytes (>0 e ≤5.242.880); largura; altura; hash_sha256 (único por inspeção); legenda (≤200, opc.); **anotacao** (obrig., 1..1000 após trim); data_captura opc.; ordem; criado_em.

**Relacionamentos:** Local 1—N Inspecao; Inspecao 1—N ItemInspecao; Inspecao 1—N FotoVistoria; ItemInspecao 0..1—N FotoVistoria; ModeloItem 1—N ItemInspecao (cópia na criação).
**Índices:** inspecao(status), inspecao(data_agendamento), inspecao(local_id), item_inspecao(inspecao_id), foto_vistoria(inspecao_id), foto_vistoria(item_inspecao_id), único (inspecao_id, hash_sha256).

**Quatro campos de texto — não confundir:** `observacoes` (cadastro, inspeção) · `observacoes_vistoria` (narrativa do que foi visto, inspeção) · `observacao` (item; obrigatória se NÃO CONFORME) · `legenda` (título curto da foto) · `anotacao` (o que foi observado na foto; obrigatória).

## 4. Regras de negócio

| Id | Regra |
|---|---|
| RN01 | Inspeção referencia um Local da lista; sem texto livre. |
| RN02 | `data_realizacao` não pode ser posterior a hoje. |
| RN03 | Código sequencial, gerado, imutável, nunca reutilizado. |
| RN04 | Fechar exige **todos** os itens com situação ≠ NAO_RESPONDIDO. |
| RN05 | Item NAO_CONFORME exige `observacao` para fechar. |
| RN06 | Resultado no fechamento: algum **crítico** NC → REPROVADA; senão algum NC → APROVADA_COM_RESSALVAS; senão APROVADA. |
| RN07 | FINALIZADA (e CANCELADA) é imutável: inspeção, itens, observações e fotos. |
| RN08 | Transições: ABERTA→EM_ANDAMENTO→FINALIZADA; ABERTA→CANCELADA (com motivo). Nenhuma outra. |
| RN09 | Checklist nasce com cópia dos 6 itens do modelo; item avulso vale só na própria inspeção; item de modelo não é removível. |
| RN10 | `resultado` só existe após o fechamento (antes: nulo, exibido "—"). |
| RN11 | Latitude/longitude do Local obrigatórias e dentro das faixas de MT. |
| RN12 | `data_agendamento` obrigatória; pode ser passada, atual ou futura. |
| RN13 | `data_realizacao` ≥ `data_agendamento`. |
| RN14 | Edição por status — ABERTA: **numero_processo**, local_id, data_agendamento, objetivo, observacoes, observacoes_vistoria · EM_ANDAMENTO: **numero_processo**, data_realizacao, observacoes, observacoes_vistoria · FINALIZADA/CANCELADA: nada. (`numero_processo` foi acrescentado em 23/10/2026.) |
| RN15 | Cancelada mantém agendamento e não tem realização. |
| RN16 | `observacoes_vistoria` = contexto do que foi visto; não substitui observação de item. |
| RN17 | `observacoes_vistoria` é opcional; não bloqueia fechamento. |
| RN18 | Editável em ABERTA e EM_ANDAMENTO; leitura nos demais. |
| RN19 | Máx. 2000 caracteres; trim; vazio vira nulo; texto puro (escape no front, quebras preservadas). |
| RN20 | Fotos: JPEG, PNG ou WebP. |
| RN21 | Máx. 5 MB por foto e 20 fotos por inspeção. |
| RN22 | Tipo validado **pelo conteúdo**, não por extensão/Content-Type. |
| RN23 | Enviar/editar/excluir foto só em ABERTA/EM_ANDAMENTO. |
| RN24 | Enviar foto não muda o status. |
| RN25 | Foto não é exigida para fechar; item NC sem foto gera só aviso na tela. |
| RN26 | EXIF removido (original e miniatura). |
| RN27 | Mesma imagem (hash) não pode repetir na mesma inspeção. |
| RN28 | Gravar arquivo→registro; se o registro falhar, apagar arquivo; excluir registro→arquivo; utilitário de verificação lista inconsistências. Validar tudo **antes** de gravar em disco. |
| RN29 | `item_id` da foto deve pertencer à mesma inspeção; remover item avulso mantém a foto sem vínculo. |
| RN30 | Exclusão de foto é física, com confirmação; sem lixeira. |
| RN31 | `anotacao` da foto é obrigatória. |
| RN32 | Anotação 1..1000 caracteres após trim; texto puro. |
| RN33 | Anotação editável só em ABERTA/EM_ANDAMENTO; nunca vazia. |
| RN34 | Anotação não influencia resultado nem fechamento; não dispensa a observação do item NC. |
| RN35 | `numero_processo` é obrigatório (trim; vazio → 422 `VALIDACAO_CAMPO`), texto livre de até 60 caracteres, não único; pode ser corrigido enquanto a inspeção estiver ABERTA ou EM_ANDAMENTO. Linhas antigas sem número continuam válidas e exigem número ao serem editadas nesse campo. |
| RN36 | A tela "Nova inspeção" permite criar um local (nome, município, tipo, latitude, longitude) via `POST /locais`, com as mesmas validações de RN11; o local criado já fica selecionado. Na rodada R2 a tela **Locais** passou a listar, cadastrar e editar locais (RN40); inativar ou excluir locais pela interface continua fora do escopo. |
| RN37 | Os cartões do Painel levam à lista da própria categoria: Inspeções = ABERTA + EM_ANDAMENTO + FINALIZADA (exclui canceladas), Pendências = ABERTA + EM_ANDAMENTO, Finalizadas = FINALIZADA; o total listado coincide com o contador. |
| RN38 | A API informa em `campos_editaveis` (no detalhe da inspeção) quais campos podem ser alterados no status atual; a interface só renderiza o que vier nessa lista (a regra RN14 fica no backend). |
| RN39 | `numero_car` é opcional e de texto livre (maiúsculas, trim, ≤60). Nenhum formato é rejeitado (SICAR, SIMCAR-MT ou outro); a tela só avisa, sem bloquear, quando não segue UF-código IBGE-código. |
| RN40 | Proprietários (0..20 por Local): nome obrigatório (≤120); telefone opcional, guardado só com dígitos, 10 ou 11 com DDD (11 a 99) e exibido como (65) 99999-9999. Erros de validação apontam a linha (`proprietarios.N.telefone`). O PUT de local substitui a lista inteira. |
| RN41 | Ao fechar, grava-se uma cópia dos dados do empreendimento (nome, município, tipo, coordenadas, CAR, proprietários e telefones) na mesma transação que muda o status. A inspeção FINALIZADA usa a cópia; antes do fechamento (e quando CANCELADA) usa os dados atuais do Local. Se a cópia falhar, o fechamento é desfeito. |
| RN42 | O número do relatório `NNNN/AAAA` é sequencial por ano (ano da data de fechamento, relógio injetável), atribuído no fechamento, único e nunca reutilizado (contador por ano que não decresce). Só existe em FINALIZADA; cancelar ou tentar fechar sem sucesso não consome número. |
| RN43 | O relatório (`GET /inspecoes/{id}/relatorio`) de inspeção finalizada é o documento numerado, com a cópia do empreendimento; nos demais status é uma **prévia**, sem número e com a marca "PRÉVIA, NÃO FINALIZADO" ("CANCELADA, NÃO FINALIZADO" quando cancelada). Seções: 1 Identificação, 2 Empreendimento, 3 Objetivo e observações, 4 Checklist (numerado, com totais e críticos não conformes destacados), 5 Registro fotográfico (imagem original, no máximo 2 por página), 6 Conclusão (resultado e a regra que o gerou). |
| RN44 | A impressão usa o navegador (CSS `@media print`, A4, sem menu nem botões); não há biblioteca de PDF no backend. Rodapé com nº do relatório, INS e aviso de sistema fictício, e "Página X de Y", saem das caixas de margem do `@page` (Chrome/Edge; Firefox pode omitir a numeração). O botão "Imprimir / Salvar PDF" só é liberado depois que as imagens carregarem. |
| RN45 | Mensagens orientativas vêm do backend: fechar inspeção ABERTA devolve 409 `TRANSICAO_INVALIDA` com "A inspeção ainda não foi iniciada. Registre a situação de pelo menos um item do checklist antes de fechar."; o detalhe traz `fechamento_bloqueado_motivo` e `registro_bloqueado_motivo` (agendamento futuro), e a tela os exibe antes de qualquer tentativa. |
| RN46 | Todo campo de formulário da interface tem `id`, `name` únicos e `label` associado (`htmlFor`). |

**Comportamentos de serviço:** o primeiro item registrado em ABERTA muda o status para EM_ANDAMENTO e preenche `data_realizacao` com hoje se vazia (ver pendência P1). Gravar observações/fotos não muda status.

## 5. Endpoints (`/api/v1`)

| Método e caminho | Função | OK | Erros |
|---|---|---|---|
| GET `/health` | vida | 200 | — |
| GET `/locais`, `/locais/{id}` | listar/detalhar locais | 200 | 404 |
| POST `/locais`, PUT `/locais/{id}` | criar/atualizar (valida RN11, RN39, RN40); o corpo aceita `numero_car` e `proprietarios[{nome, telefone}]`; a resposta traz `telefone` (dígitos) e `telefone_formatado`; também usado pela tela "Nova inspeção" (RN36) | 201/200 | 404, 422 |
| POST `/inspecoes` | cadastrar (exige `numero_processo`; gera código + 6 itens) | 201 | 422 |
| GET `/inspecoes` | filtros `status` (**repetível**: `?status=ABERTA&status=EM_ANDAMENTO`), `numero_processo` (contém, sem diferenciar maiúsculas; `%` e `_` valem como texto), `data_inicio`, `data_fim` (sobre agendamento), `local_id`, `pagina`, `tamanho`; ordenação agendamento desc | 200 | 422 |
| GET `/inspecoes/{id}` | detalhe (local, itens, fotos, resumo) | 200 | 404 |
| GET `/inspecoes/{id}/relatorio` | relatório estruturado (RN43): `previa`, `marca_dagua`, `numero_relatorio`, `titulo`, `identificacao`, `empreendimento`, `objetivo`, `checklist {itens, totais}`, `fotos` (URL do original), `conclusao {resultado, regra}` | 200 | 404 |
| PATCH `/inspecoes/{id}` | edição por status (RN14) | 200 | 404, 409, 422 |
| POST `/inspecoes/{id}/cancelar` | `{motivo}` | 200 | 404, 409, 422 |
| POST `/inspecoes/{id}/fechar` | fecha e calcula resultado | 200 | 404, 409, 422 |
| GET/POST `/inspecoes/{id}/itens` | listar / adicionar avulso | 200/201 | 404, 409, 422 |
| PATCH `/inspecoes/{id}/itens/{item_id}` | situação e observação | 200 | 404, 409, 422 |
| DELETE `/inspecoes/{id}/itens/{item_id}` | remove avulso | 204 | 404, 409 |
| POST `/inspecoes/{id}/fotos` | multipart: `arquivo`, `anotacao`, `legenda?`, `item_id?`, `data_captura?` (uma por requisição) | 201 | 404, 409, 413, 415, 422 |
| GET `/inspecoes/{id}/fotos`, `/fotos/{foto_id}` | metadados | 200 | 404 |
| GET `/inspecoes/{id}/fotos/{foto_id}/arquivo?versao=miniatura\|original` | binário (`nosniff`) | 200 | 404 |
| PATCH `/inspecoes/{id}/fotos/{foto_id}` | `anotacao`, `legenda`, `item_id`, `ordem` | 200 | 404, 409, 422 |
| DELETE `/inspecoes/{id}/fotos/{foto_id}` | exclui | 204 | 404, 409 |
| GET `/indicadores` | `{inspecoes, pendencias, finalizadas, gerado_em}` | 200 | — |
| GET `/exportacao/inspecoes.csv` | CSV | 200 | — |
| POST `/utilitarios/carregar-exemplos` | seed | 201 | 409 |
| GET `/utilitarios/verificar-fotos` | consistência registro/arquivo | 200 | — |

**Listas:** envelope `{dados, total, pagina, tamanho}`; a lista de inspeções traz `qtd_fotos` e o local resumido, sem itens.
**Detalhe:** inclui `local` (com lat/long como número), `itens`, `fotos` (com `url_miniatura`/`url_original`), `resumo_itens {total, respondidos, nao_conformes}` e contagem de fotos por item. Inclui também `numero_processo` e `campos_editaveis` (RN38). A lista de inspeções traz `numero_processo`. Também traz `empreendimento` (cópia do fechamento quando finalizada; dados atuais do Local nos demais status), `numero_relatorio` (só finalizada), `fechamento_bloqueado_motivo` e `registro_bloqueado_motivo` (RN45).
**CSV:** colunas código, **numero_processo**, local, latitude, longitude, data_agendamento, data_realizacao, status, resultado, observacoes_vistoria, qtd_fotos; delimitador `;`, UTF-8 com BOM, aspas e quebras de linha tratadas; textos livres que começam com `=`, `+`, `-` ou `@` recebem apóstrofo inicial (proteção contra fórmulas em planilhas).

## 6. Contrato de erro (único)

```
{ "erro": { "codigo": "...", "mensagem": "...", "detalhes": [ { "campo": "...", "mensagem": "..." } ] } }
```

| HTTP | codigo | Quando |
|---|---|---|
| 422 | VALIDACAO_CAMPO | campo ausente/inválido/acima do limite (agendamento, local, anotação, legenda, observacoes_vistoria...) |
| 422 | DATA_REALIZACAO_FUTURA | RN02 |
| 422 | DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO | RN13 |
| 422 | COORDENADA_FORA_DE_MT | RN11 |
| 422 | FECHAMENTO_BLOQUEADO | RN04/RN05; `detalhes` lista cada item |
| 422 | ITEM_NAO_PERTENCE_A_INSPECAO | RN29 |
| 409 | TRANSICAO_INVALIDA | RN08 |
| 409 | INSPECAO_IMUTAVEL | RN07/RN23 |
| 409 | CAMPO_NAO_EDITAVEL_NO_STATUS | RN14 |
| 409 | ITEM_DE_MODELO_NAO_REMOVIVEL | RN09 |
| 409 | LIMITE_FOTOS_EXCEDIDO | RN21 |
| 409 | FOTO_DUPLICADA | RN27 |
| 409 | BANCO_JA_POVOADO | seed com dados existentes |
| 413 | FOTO_TAMANHO_EXCEDIDO | RN21 |
| 415 | FOTO_FORMATO_INVALIDO | RN20/RN22 |
| 404 | NAO_ENCONTRADO / FOTO_ARQUIVO_AUSENTE | id inexistente / arquivo ausente em disco |
| 500 | ERRO_INTERNO | sem detalhes técnicos |

Ordem de validação no envio de foto: estado da inspeção (409) → campos e arquivo (422/413/415) → limite e duplicidade (409) → só então gravar.

## 7. Indicadores (consulta única, portátil)

- **Inspeções** = total com status ≠ CANCELADA.
- **Pendências** = status ∈ {ABERTA, EM_ANDAMENTO}.
- **Finalizadas** = status = FINALIZADA.
- Invariante: Pendências + Finalizadas = Inspeções. Esperado nos dados de exemplo: **5 / 2 / 3**.
- Cada cartão do Painel é um link para a lista da categoria (RN37); a lista mostra o filtro ativo e o total.

## 8. Telas

| Rota | Tela | Conteúdo |
|---|---|---|
| `/` | Painel | 3 cartões **clicáveis** (cada um abre a lista da categoria); atalhos "Nova inspeção" e "Ver pendências"; botões "Carregar exemplos" e "Exportar CSV" |
| `/inspecoes` | Lista | código, **processo**, local, agendamento, realização ("—"), status, resultado, fotos, **ações (Editar, só em Aberta/Em andamento)**; filtros de status (inclui os grupos "Todas, exceto canceladas" e "Pendências"), **busca por número do processo** e período; mostra o filtro ativo e o total |
| `/inspecoes/nova` | Nova | **número do processo**, local (com lat/long somente leitura) e botão **"+ Novo local"** (modal, RN36), agendamento, objetivo, observações |
| `/inspecoes/:id` | Detalhe/execução | cabeçalho (status, **processo**, datas, local); botão **Editar inspeção** quando houver campos editáveis; cartão **Empreendimento** (CAR "Não informado" quando vazio, proprietários) com a origem dos dados; botão **Gerar relatório** em qualquer status; avisos de início da inspeção e de agendamento futuro; "Checklist concluído em dd/mm/aaaa hh:mm" nas finalizadas; checklist; item avulso; **observações da vistoria** (contador x/2000); **fotos** (lista de pendentes com anotação obrigatória por foto, galeria, visualizador com anotação); Fechar e Cancelar (modais); somente leitura em FINALIZADA/CANCELADA |
| `/inspecoes/:id/editar` | Editar | formulário com os campos de `campos_editaveis` (RN38) editáveis e os demais como texto; envia só o que mudou; erros da API exibidos sem perder o digitado |
| `/inspecoes/:id/relatorio` | Relatório | relatório numerado e imprimível (RN43, RN44); prévia com marca quando não finalizada; botão "Imprimir / Salvar PDF" |
| `/locais` | Locais | lista (nome, município, tipo, CAR, proprietários com telefone formatado, coordenadas) e botão "Novo local" |
| `/locais/novo`, `/locais/:id/editar` | Local | formulário com os campos do local, CAR e lista de proprietários (adicionar/remover); o mesmo formulário aparece no modal "Novo local" de Nova inspeção |

Toda tela trata estados: carregando, vazio, erro (`mensagem` + `detalhes`). No fechamento bloqueado, destacar os itens citados. No modal de fechar: resumo das observações da vistoria, "Fotos anexadas: n" e aviso (não bloqueante) para item NC sem foto.

## 9. Pendências e decisões em aberto

| Id | Pendência | Padrão adotado até decisão do dono do produto |
|---|---|---|
| **P1** | **Conflito de datas:** registrar o 1º item de inspeção agendada para o futuro preencheria `data_realizacao`=hoje < agendamento (viola RN13), e usar o agendamento violaria RN02. | **Bloquear**: 422 `DATA_REALIZACAO_ANTERIOR_AO_AGENDAMENTO` com mensagem "Vistoria agendada para dd/mm/aaaa; reagende (inspeção Aberta) ou aguarde". Exemplo: INS-005 (agend. 28/10) não aceita item até 28/10 ou reagendamento. |
| P2 | Anotação da foto obrigatória foi **interpretação** de "cada imagem terá uma anotação". | Obrigatória (RN31). Para relaxar: remover RN31, CA61 e CA62. |
| P3 | Fechar inspeção ABERTA. | Só fecha se EM_ANDAMENTO (senão 409 `TRANSICAO_INVALIDA`). |
| P4 | Voltar um item para NAO_RESPONDIDO. | Permitido enquanto a inspeção não for FINALIZADA/CANCELADA. |
| P5 | Cancelar inspeção EM_ANDAMENTO. | Não permitido (RN08: só ABERTA). |
| P6 | Fotos de inspeção cancelada. | Mantidas e consultáveis (somente leitura). |
| P7 | "Inspeções" no painel exclui canceladas. | Confirmado no escopo; manter. |
| P8 | Backup das fotos. | Manual (`.db` + `data/fotos/`); automático está fora do escopo. |
| P9 | Numeração de CAs. | CA01–CA73 são estáveis; **não renumerar**. Itens "ajustados" valem na versão consolidada da seção 11. |
| P10 | Licença do repositório e visibilidade no GitHub. | Pendente (dono do produto decide na S4). |
| P11 | Versões exatas de Python/Node. | **Resolvida:** Python 3.12 e Node 22 (CI com Node 20), registradas no README. |
| P12 | Regras do número do processo (23/10/2026). | Decisão do usuário: obrigatório e texto livre; filtro por número na lista. Decisões minhas: máx. 60 caracteres, não único, editável em ABERTA/EM_ANDAMENTO, coluna logo após `codigo` no CSV. Sem validação de formato (`SEMA-PRO-AAAA/NNNNN` é só exemplo). |
| P13 | Cadastro de locais pela interface (23/10/2026). | Criação (R1, RN36) e edição (R2, tela Locais) passaram ao escopo. Inativação e exclusão continuam fora. |
| P14 | Implantação (23/10/2026). | Frontend na Vercel (`https://unidade-8-desafio-21.vercel.app`) com backend local via `VITE_API_URL` e `CORS_ORIGINS`; os dados ficam no computador do usuário. Backend em nuvem exigiria PostgreSQL e armazenamento de objetos. |
| P15 | Formato do CAR (23/10/2026). | Decisão do usuário: texto livre, nunca rejeita formato; aviso só informativo. |
| P16 | Legado da rodada R2. | Decisão do usuário: ao subir a API, finalizadas antigas recebem a cópia do **Local atual** (limitação: não é o Local do dia do fechamento) e número de relatório na ordem do fechamento. |
| P17 | `VITE_API_URL` na Vercel. | Mantido em `http://127.0.0.1:8000` (backend local): o site só funciona no computador do usuário. Backend em nuvem exigiria PostgreSQL e armazenamento de objetos. |
| PB1 | **Aguarda decisão.** Vistoria antes da data agendada (RN13/P1). | Padrão atual: (a) manter o bloqueio, com o aviso preventivo da tela. Alternativas: (b) ajustar o agendamento para hoje guardando o original (coluna nova); (c) permitir realização anterior ao agendamento com aviso (quebra o CHECK de datas). |
| PB2 | **Aguarda decisão.** Data de preenchimento por item (`respondido_em`). | Não implementado. Exigiria ADD COLUMN (o mecanismo de migração leve já existe); `data_realizacao` + `fechado_em` bastam para o relatório atual. |
| PB3 | **Aguarda decisão.** Exportação dos itens do checklist. | Não implementado. Proposta: CSV separado `GET /exportacao/itens.csv`, uma linha por item, sem alterar o CSV atual. |

## 10. Status das sprints (atualizar a cada entrega)

- [ ] M0 — Documentação (não feita: docs/requisitos.md, criterios-aceite.md, ADRs e migracao-postgresql.md ainda não existem; este handoff continua sendo a fonte de requisitos)
- [x] S0 — Estrutura, ambiente e Git
- [x] S1 — Banco + API CRUD (A: inspeções/itens/locais [x] · B: fotos [x])
- [x] S2 — Frontend e integração (A: base/lista/nova/checklist · B: observações e fotos)
- [x] S3 — Dashboard com dados reais (+ exemplos e CSV)
- [~] S4 — Testes, correções, README e GitHub (suítes, E2E e deploy do frontend feitos; faltam a matriz CA01–CA85 completa e a decisão de licença/P10)
- [x] R1 — Rodada de melhorias pós-uso (23/10/2026): cartões clicáveis (RN37), botão/página Editar e `campos_editaveis` (RN38), número do processo (RN35, migração leve do banco), filtro por número, `status` repetível na lista e criação de local pela tela (RN36).
- [x] R2 — Correções de usabilidade (A1–A5), dados do empreendimento (CAR e proprietários, tela Locais), cópia no fechamento e relatório de vistoria numerado e imprimível (RN39–RN46). A Parte B ficou só como opções (PB1–PB3).

Evidências das rodadas: `docs/evidencias/R1-melhorias.md` e `docs/evidencias/R2-melhorias.md` (CA → teste; PDFs do relatório em `docs/evidencias/`).

**Última verificação (23/10/2026):** backend `pytest -q` = **334 passed**; frontend `npm test -- --run` = **124 passed** e `npm run build` ok; E2E Playwright = **14 passed** (40 telas em `docs/evidencias/telas/` e 2 PDFs do relatório).

Plano detalhado, prompts e verificações: `docs/PLANO_EXECUTAVEL.md`.

## 11. Critérios de aceite consolidados (versão final de cada CA)

**Cadastro (RF01).** CA01 cadastro válido cria Aberta, código sequencial, 6 itens NAO_RESPONDIDO e realização vazia · CA02 sem local → 422 · CA03 realização futura → 422; agendamento futuro aceito · CA04 códigos consecutivos e distintos · CA29 sem agendamento → 422 · CA30 agendamento 28/10/2026 aceito.
**Itens (RF02).** CA05 situação gravada e visível ao reabrir · CA06 1º item: Aberta→Em andamento · CA07 item avulso só na própria inspeção · CA08 itens de Finalizada/Cancelada não alteráveis · CA31 1º item preenche realização com hoje (sujeito a P1) · CA32 realização < agendamento → 422 · CA33 agendamento editável só em Aberta.
**Fechamento (RF03).** CA09 item não respondido bloqueia e lista · CA10 NC sem observação bloqueia · CA11 sem NC → Aprovada · CA12 NC não crítico → Aprovada com ressalvas · CA13 NC crítico → Reprovada · CA14 Finalizada, `fechado_em` preenchido, edição bloqueada.
**Consulta (RF04).** CA15 filtro de status · CA16 filtro de período inclusivo (sobre agendamento) · CA17 detalhe mostra todos os itens · CA34 duas datas, "—" quando vazia.
**Indicadores (RF05).** CA18 exemplos → 5/2/3 · CA19 fechar INS-004 → 1/4 sem recarregar · CA20 cancelar INS-005 reduz Inspeções e Pendências em 1 · CA21 Pend + Final = Inspeções.
**Persistência/Exportação (RF06).** CA22 dados persistem após reiniciar · CA23/CA28 CSV com colunas da seção 5 · CA24 carga de exemplos popula 4 locais, 6 itens modelo, 5 inspeções, observações da vistoria e 9 fotos com anotações.
**Locais.** CA25 4 locais com coordenadas · CA26 latitude −25 → 422 · CA27 detalhe mostra lat/long.
**Observações da vistoria.** CA35 500 caracteres gravados sem mudar status · CA36 em Aberta aceito · CA37 2000 aceito, 2001 → 422 · CA38 só espaços vira vazio ("—") · CA39 em Finalizada/Cancelada → 409 · CA40 fechar sem o campo é permitido · CA41 `<script>` exibido literal, quebras preservadas, CSV com aspas corretas.
**Fotos.** CA42 JPEG válido → 201 com miniatura · CA43 PNG e WebP aceitos · CA44 GIF → 415 · CA45 texto renomeado `.jpg` → 415 · CA46 5.242.880 B aceito, 5.242.881 → 413 · CA47 20ª aceita, 21ª → 409 · CA48 duplicada → 409 (outra inspeção aceita) · CA49 EXIF/GPS removido no original e na miniatura · CA50 foto em Aberta mantém status · CA51 galeria imutável em Finalizada/Cancelada (409), consulta ok · CA52 item de outra inspeção → 422 · CA53 remover item avulso mantém a foto sem vínculo · CA54 legenda 200 ok, 201 → 422 · CA55 excluir remove registro, original e miniatura · CA56 fotos persistem · CA57 miniatura ≤ 320 px, original íntegro · CA58 lista mostra 3/2/2/2/0 e CSV `qtd_fotos` · CA59 fechar sem fotos permitido (aviso só se item NC sem foto) · CA60 verificação reporta arquivo apagado e arquivo solto; zero em banco limpo.
**Anotação da foto.** CA61 sem anotação → 422, nada gravado em disco/banco · CA62 só espaços → 422 · CA63 1000 ok, 1001 → 422 · CA64 1 caractere ok · CA65 trim aplicado · CA66 edição persiste · CA67 editar para vazio → 422, texto anterior mantido · CA68 editar em Finalizada/Cancelada → 409 · CA69 UI: "Enviar" desabilitado com anotação faltando · CA70 falha parcial preserva anotações e grava as válidas · CA71 `<script>` literal com quebras · CA72 anotação não altera resultado (INS-003 segue Reprovada) · CA73 excluir foto remove a anotação.
**Rodada R1 (CA74–CA85, numeração nova; CA01–CA73 seguem estáveis, P9).** CA74 cadastro sem `numero_processo` (ausente, vazio ou só espaços) → 422 com campo `numero_processo` · CA75 número gravado com trim, 60 caracteres aceito e 61 → 422, texto livre e repetido entre inspeções aceito · CA76 número editável em Aberta e Em andamento (vazio → 422, valor anterior mantido) e em Finalizada/Cancelada → 409 · CA77 detalhe devolve `campos_editaveis` conforme o status (Aberta: 6 campos; Em andamento: 4; Finalizada/Cancelada: nenhum) · CA78 `GET /inspecoes?status=A&status=B` une os status com total e paginação corretos · CA79 filtro `numero_processo` por trecho, sem diferenciar maiúsculas, com `%` e `_` como texto e sem injeção · CA80 cada cartão do Painel abre a lista da categoria e o total listado coincide com o contador (Inspeções exclui canceladas) · CA81 botão Editar na lista e no detalhe só em Aberta/Em andamento · CA82 página de edição permite só os campos de `campos_editaveis`, envia só o que mudou e mostra erros 409/422 sem perder o digitado · CA83 "Novo local" cria local válido já selecionado, exige campos, recusa coordenada fora de MT (erro da API) e cancela sem criar · CA84 banco criado antes do campo ganha a coluna `numero_processo` sem perder dados e a migração é idempotente · CA85 CSV traz `numero_processo` após `codigo` e neutraliza texto que começa com `=`, `+`, `-` ou `@`.
**Rodada R2 (CA86–CA110, numeração nova; CA01–CA85 seguem estáveis, P9).** CA86 fechar inspeção Aberta devolve mensagem orientativa (código `TRANSICAO_INVALIDA`) e o botão fica desabilitado com o motivo · CA87 aviso, acima do checklist de inspeção Aberta, de que só registrar a situação de um item inicia a inspeção · CA88 aviso preventivo de agendamento futuro com link para editar e seletores de situação desabilitados, mantendo o bloqueio da API · CA89 todo campo de formulário com id, name únicos e label associado · CA90 rótulos de datas explicados e "Checklist concluído em dd/mm/aaaa hh:mm" na finalizada · CA91 CAR opcional, em maiúsculas e sem espaços nas pontas, nenhum formato rejeitado (acima de 60 → 422) · CA92 proprietário exige nome; telefone com 10 ou 11 dígitos e DDD, guardado só com dígitos e exibido (65) 99999-9999; erro aponta a linha; máximo de 20 · CA93 PUT de local substitui a lista de proprietários (lista vazia limpa) e um PUT inválido não altera nada · CA94 tela Locais lista, cadastra e edita, com adicionar e remover proprietários · CA95 detalhe da inspeção mostra o empreendimento (CAR "Não informado" quando vazio) · CA96 editar o Local depois do fechamento não altera a inspeção finalizada; antes do fechamento ela usa os dados atuais · CA97 falha ao gravar a cópia desfaz o fechamento · CA98 preenchimento do legado idempotente e sem sobrescrever cópia existente · CA99 número de relatório `NNNN/AAAA` sequencial, sem repetição e com índice único · CA100 virada de ano reinicia a sequência de cada ano sem reutilizar números · CA101 cancelar, fechamento bloqueado e gerar prévia não consomem número · CA102 relatório finalizado com as 6 seções na ordem, checklist numerado com totais e críticos não conformes destacados · CA103 fotos numeradas com imagem original, legenda, anotação, item vinculado (ou "Sem vínculo") e data de captura · CA104 conclusão com o resultado e a regra aplicada · CA105 prévia sem número, com a marca "PRÉVIA, NÃO FINALIZADO" · CA106 impressão A4 sem menu nem botões, rodapé e "Página X de Y" em todas as páginas e no máximo 2 fotos por página sem corte (evidência: PDFs gerados pelo E2E) · CA107 "Imprimir / Salvar PDF" só habilita com as imagens carregadas · CA108 seed, testes e capturas só com dados fictícios (proprietários, telefones, CAR) · CA109 migração leve idempotente de `numero_car`, `proprietario`, `empreendimento_json`, `numero_relatorio` (índice único) e `contador_relatorio` em banco antigo · CA110 fotos de exemplo com o texto "FOTO FICTÍCIA — INS-00X #n" legível.

## 12. Dados de exemplo (seed)

**Locais:** L1 Fazenda Horizonte Azul / Vila Nova do Cerrado / Propriedade rural / −10,42318, −58,71264 · L2 Serraria Ipê Dourado / Porto das Águas / Indústria madeireira / −11,21456, −58,30977 · L3 Posto Rio Claro / São Tomé do Norte / Posto de combustíveis / −9,71234, −58,12845 · L4 Reserva Mata Ciliar Beta / Campo Verde do Sul / Área de preservação / −10,91507, −59,46288.

**Modelo de checklist (crítico):** 1 Licença ambiental fictícia apresentada e dentro da validade (sim) · 2 Área de preservação delimitada e sem supressão (sim) · 3 Armazenamento de resíduos adequado · 4 Sinalização de segurança visível · 5 Registro de manejo/atividade atualizado · 6 Destinação de efluentes regular (sim).

| Código | Local | Agend. | Realiz. | Status | Resultado | Itens |
|---|---|---|---|---|---|---|
| INS-001 | L1 | 05/10/2026 | 06/10/2026 | Finalizada | Aprovada | 1–6 Conforme |
| INS-002 | L2 | 13/10/2026 | 13/10/2026 | Finalizada | Aprovada com ressalvas | 4 e 5 NC (com obs.); demais Conforme |
| INS-003 | L3 | 14/10/2026 | 15/10/2026 | Finalizada | Reprovada | 6 (crítico) NC com obs.; demais Conforme |
| INS-004 | L4 | 20/10/2026 | 20/10/2026 | Em andamento | — | 1–3 Conforme; 4–6 não respondidos |
| INS-005 | L1 | 28/10/2026 | — | Aberta | — | nenhum respondido |

**Números de processo do seed (fictícios):** INS-001 `SEMA-PRO-2026/10001` … INS-005 `SEMA-PRO-2026/10005`.

**Empreendimento do seed (100% fictício, LGPD):** L1 com CAR `MT-5107925-00000000000000000000000000000001` e proprietários "Proprietário Fictício Um" (65) 90000-0001 e "Proprietária Fictícia Dois" (65) 90000-0002; L2 com "Madeireira Fictícia Ltda." (65) 90000-0003; L3 sem CAR nem proprietários; L4 com CAR `MT-5107925-00000000000000000000000000000004` e "Proprietário Fictício Quatro" sem telefone. As finalizadas INS-001 a INS-003 já nascem com a cópia do empreendimento e os números `0001/2026`, `0002/2026` e `0003/2026`.

**Observações da vistoria:** INS-001 "Propriedade em boas condições gerais. Documentação apresentada pelo responsável fictício no ato da vistoria. Sem pendências visíveis." · INS-002 "Pátio com acúmulo moderado de serragem junto ao galpão. Placas de segurança parcialmente desgastadas. Registro de manejo com atualização atrasada." · INS-003 "Odor de combustível na área de descarga. Caixa separadora de efluentes com sinais de transbordamento. Responsável ausente no horário da vistoria." · INS-004 "Acesso pela estrada vicinal em bom estado. Nascente delimitada com cerca; vegetação ciliar preservada no trecho norte. Trecho sul ainda não percorrido." · INS-005 vazio.

**Fotos (9, geradas por programa com o texto "FOTO FICTÍCIA — INS-00X #n"):**
INS-001 #1 "Vista geral da sede: construções em boas condições e área ao redor limpa." · #2 "Documentação fictícia apresentada pelo responsável, disposta sobre a mesa no ato da vistoria." · #3 "Divisa da propriedade com cerca íntegra e sem sinais de invasão." (sem item)
INS-002 #1 item 4 "Placa de segurança na entrada do galpão com tinta desgastada e texto parcialmente ilegível." · #2 item 5 "Livro de registro de manejo com última anotação datada de meses antes da vistoria."
INS-003 #1 item 6 "Caixa separadora com sinais de transbordamento junto à base e resíduo oleoso no solo ao redor." · #2 item 6 "Área de descarga com manchas escuras no piso, compatíveis com derramamento recorrente."
INS-004 #1 "Nascente cercada, com vegetação ciliar preservada no trecho norte." · #2 "Estrada vicinal de acesso em boas condições de trafegabilidade."
INS-005: sem fotos.

**Dados negativos para testes:** sem agendamento; realização 24/10/2026; realização anterior ao agendamento; latitude −25,00000; fechar INS-004 (3 pendentes → 3 detalhes); item NC sem observação; PATCH em INS-001; PATCH de agendamento em INS-004; DELETE de item de modelo; imagens: JPEG 800×600, PNG, WebP, JPEG com EXIF/GPS fictício, 5.242.880 B e 5.242.881 B, GIF, texto renomeado `.jpg`, arquivo vazio, duplicata, 21 imagens distintas, nome com acento e `<script>`; textos: 0/1/1000/1001 caracteres, só espaços, acentos/aspas/quebras, `<script>alert(1)</script>`.

## 13. Fora do escopo do MVP

Login/perfis com permissão real; múltiplos usuários; rede/nuvem/sincronização; app móvel; tela de edição de modelos de checklist; inativação e exclusão de locais (criação e edição passaram ao escopo, RN36 e RN40); reabertura de inspeção finalizada; histórico/auditoria; hora do agendamento, calendário, lembretes, alerta de atraso, reagendamento com histórico; geração de PDF no servidor (o relatório é impresso pelo navegador); relatórios consolidados; gráficos avançados; mapa/GPS/geolocalização; leitura de EXIF; câmera; edição/rotação/marcação sobre imagem; vídeo/PDF anexos; marca d'água; compressão avançada; lixeira; backup automático; busca textual; integração com sistemas reais.

## 14. Mapa de pastas alvo

```
inspecoes-simuladas/
├── README.md  HANDOFF_CLAUDE_CODE.md  CLAUDE.md(opcional, gerado por /init)  .gitignore
├── .github/workflows/ci.yml
├── docs/ (evidencias/ [S1A.md, S1B.md, S2-S3-E2E.md, telas/], PLANO_EXECUTAVEL.md; requisitos.md, criterios-aceite.md, adr/ e migracao-postgresql.md ainda não escritos)
├── backend/ (pyproject.toml, .env.example, data/ [ignorado], app/{main,config,database,clock,errors}.py,
│            models/ schemas/ domain/ repositories/ services/ storage/ routers/ seed/, tests/{unit,service,api,fixtures})
├── frontend/ (package.json, vite.config.ts, vercel.json, src/{api,pages,components,hooks,utils,tests})
└── e2e/ (Playwright: fluxo completo e geração das telas de evidência)
```
`.gitignore` obrigatório: `*.db`, `backend/data/`, `.env`, `venv/`, `.venv/`, `node_modules/`, `dist/`, `__pycache__/`.

## 15. Como rodar (confirmado)

Instalação, execução, variáveis de ambiente, testes e publicação do frontend estão no `README.md` (comandos executados neste repositório). Resumo: backend `uvicorn app.main:app --host 127.0.0.1 --port 8000` em `backend/`; frontend `npm run dev` em `frontend/` (porta 5173); testes `pytest -q`, `npm test -- --run`, `npm run build` e `npx playwright test` (em `e2e/`).

## 16. Alterações posteriores ao escopo original (histórico)

| Data | Alteração | Referências |
|---|---|---|
| 23/10/2026 | Número do processo (obrigatório, texto livre) com filtro por número; editável em Aberta/Em andamento | RN35, RN14, CA74–CA79, CA84, CA85, P12 |
| 23/10/2026 | Cartões do Painel clicáveis e `status` repetível na lista (grupos Inspeções/Pendências/Finalizadas) | RN37, CA78, CA80 |
| 23/10/2026 | Botão e página Editar guiados por `campos_editaveis` | RN38, CA77, CA81, CA82 |
| 23/10/2026 | Criação de local pela tela "Nova inspeção" (a edição veio com a tela Locais na R2; inativação e exclusão seguem fora) | RN36, CA83, P13 |
| 23/10/2026 | Frontend publicado na Vercel com backend local | P14, README |
| 23/10/2026 | Correções de usabilidade: mensagens orientativas, avisos de início e de agendamento futuro, id/name/label nos campos, rótulos das datas | RN45, RN46, CA86–CA90 |
| 23/10/2026 | CAR e proprietários nos Locais, com tela Locais e cartão Empreendimento no detalhe | RN39, RN40, CA91–CA95, P15 |
| 23/10/2026 | Cópia dos dados do empreendimento no fechamento, com preenchimento do legado | RN41, CA96–CA98, P16 |
| 23/10/2026 | Relatório de vistoria numerado (NNNN/AAAA), prévia e impressão A4 pelo navegador | RN42–RN44, CA99–CA107 |

Efeito colateral a lembrar: o contrato de `POST /inspecoes` mudou (campo obrigatório) e o CSV ganhou uma coluna; só o frontend deste repositório consome a API. Na R2, `PUT /locais` passou a substituir a lista de proprietários (um PUT sem `proprietarios` apaga os existentes) e o JSON do local e do detalhe ganhou novos campos.
