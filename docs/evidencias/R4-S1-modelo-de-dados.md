# R4 · Sprint S1 — modelo de dados e migração (E1, E2 e migração do E7)

Rodada R4 (nome combinado com o usuário; o texto original a chamava de R3, nome já usado pela exportação dos itens). Branch `r4-capa-sema-corpo-relatorio`. Dados 100% fictícios.

## Verificação

| Suíte | Comando | Antes | Depois |
|---|---|---|---|
| Backend | `cd backend && pytest -q` | 348 | **405** |
| Frontend | `cd frontend && npm test -- --run` | 125 | **125** (sem mudança nesta sprint) |
| E2E | `cd e2e && npx playwright test` | 14 | **14** |

## O que mudou

**E1 — dados da inspeção** (`Inspecao`, tabelas `equipe_membro` e `ato_lavrado`)
- Interessado: `interessado_orgao`, `interessado_unidade`, `interessado_comarca`, `interessado_requerente` (todos opcionais; vazio = "Demanda interna / de ofício", exibição nas sprints S3/S4).
- Protocolo: reaproveita `numero_processo`.
- Assunto: `assunto_tipo` (lista fixa em `domain/constantes.py`, com "Outro") e `assunto_outro` (obrigatório só quando "Outro"; descartado nos demais tipos).
- Equipe técnica: lista de nome, cargo e órgão, até 20; a API substitui a lista inteira no `PATCH`. **Fechar exige pelo menos 1 membro** (422 `FECHAMENTO_BLOQUEADO`, detalhe `campo: "equipe"`).
- Providências: `providencias_texto` (≤2000) e lista de atos (tipo da lista fixa + número opcional, ≤40).
- `numero_relatorio_sema` (≤40), opcional. O `numero_relatorio` NNNN/AAAA continua e passa a ser a "Ref. interna" na exibição.
- RN14: os campos novos são editáveis em Aberta e Em andamento. Na Finalizada só `numero_relatorio_sema` e o número dos atos já listados (tipo e quantidade não mudam; ato identificado por `id`); `atualizado_em` é atualizado; qualquer outro campo continua `409 INSPECAO_IMUTAVEL`. `campos_editaveis` da finalizada passa a ser `["atos","numero_relatorio_sema"]`. Cancelada segue imutável.

**E2 — empreendimento e responsável**
- Local: `logradouro`, `uf` (padrão MT) e `cep` (8 dígitos). O município reaproveita `municipio`, e o nome fantasia reaproveita `nome` (só o rótulo muda, nas telas da S2).
- Responsável: `cpf_cnpj` (só dígitos, dígitos verificadores conferidos) e endereço para correspondência (`corr_*`). O atalho "mesmo endereço do empreendimento" é a flag `correspondencia_mesmo_endereco` (regra no backend: copia logradouro, município, UF e CEP do Local; número, complemento e bairro continuam do usuário).
- Saída traz `cpf_cnpj_formatado`, `cep_formatado` e `corr_cep_formatado` (máscaras `000.000.000-00`, `00.000.000/0000-00`, `00.000-000`).
- A cópia do fechamento (C2) leva todos os campos novos.

**E7 — migração**
- `database._garantir_colunas` acrescenta as colunas novas de `inspecao`, `local` e `proprietario` (idempotente); as tabelas novas nascem pelo `create_all`. Inspeções antigas ficam com os campos novos nulos e a equipe/atos vazios; o detalhe e o relatório continuam abrindo.
- Backup antes de migrar: copiar `backend/data/` (a pasta fica fora do Git).

## Testes novos (57) e testes alterados

Novos: `tests/unit/test_documento.py` (CPF/CNPJ/CEP/UF), `tests/unit/test_migracao_r4.py` (banco anterior à R4 e legado abrindo), `tests/api/test_r4_locais.py` (endereço, CPF/CNPJ, correspondência, atalho, cópia do fechamento, seed) e `tests/api/test_r4_inspecao.py` (E1 completo, fechar sem equipe, edição pós-fechamento só do número dos atos e do nº SEMA).

Alterados, por mudança de regra e não por enfraquecimento:
- Os auxiliares que criam e fecham inspeção (`test_api_fotos`, `test_api_inspecoes`, `test_copia_fechamento`, `test_relatorio`, `test_inspecao_service`) passaram a enviar 1 membro na `equipe`, porque agora ela é obrigatória para fechar.
- `test_numero_processo::test_campos_editaveis_vem_da_api_por_status`: listas esperadas incluem os campos novos, e a Finalizada passa de `[]` para `["atos","numero_relatorio_sema"]`.
- `test_copia_fechamento::test_copia_fica_gravada_no_banco_como_json_completo` e `test_locais_empreendimento::test_criar_com_car_e_proprietarios`: o contrato ganhou campos (as asserções originais continuam valendo para os campos antigos).

Seed: todas as inspeções de exemplo têm equipe; INS-001 e INS-002 têm interessado MP fictício; INS-002 e INS-003 têm atos (um sem número); locais com endereço, CPF/CNPJ fictícios válidos e correspondência.

## Limitações e próximos passos
- O front ainda não envia nem exibe os campos novos (S2). Fechar uma inspeção criada pela tela exige a equipe, que só a S2 permite informar; os exemplos já vêm com equipe.
- `numero_relatorio_sema` e atos só podem ser editados pós-fechamento pela API até a S3/S4.
