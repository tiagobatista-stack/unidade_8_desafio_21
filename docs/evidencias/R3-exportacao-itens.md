# Evidências — R3 (decisões da Parte B e exportação dos itens do checklist)

Data: 2026-10-23. Regras: `HANDOFF_CLAUDE_CODE.md` (RN47, CA111–CA116, PB1–PB3).

## Decisões do usuário

| Item | Decisão | Efeito |
|---|---|---|
| B1 — vistoria antes da data agendada | manter a regra atual (a) | nenhuma mudança; o aviso preventivo da R2 resolve a confusão. A opção (c) foi descartada: quebraria o CHECK `data_realizacao >= data_agendamento` |
| B2 — `respondido_em` por item | adiar | `data_realizacao` e `fechado_em` já cobrem o relatório |
| B3 — exportação dos itens | implementar como proposto | arquivo separado, sem mexer no CSV atual |

## O que foi implementado (B3)

`GET /api/v1/exportacao/itens.csv` (download `itens-checklist.csv`) e botão **Exportar itens (CSV)** no Painel.

- Uma linha por item de cada inspeção, incluindo canceladas e itens avulsos; inspeções na ordem do id, itens na ordem do checklist.
- Colunas: `codigo_inspecao; numero_processo; local; status_inspecao; resultado_inspecao; item_numero; item_descricao; critico; situacao; observacao; origem; qtd_fotos`.
- `;` como delimitador, UTF-8 com BOM (Excel), aspas e quebras de linha tratadas, texto livre que começa com `=`, `+`, `-` ou `@` recebe apóstrofo.
- `item_numero` é a posição no checklist (a mesma numeração do relatório); `critico` sai `sim`/`nao`; `situacao` e `origem` saem como código da API; `qtd_fotos` conta só as fotos vinculadas ao item.
- O CSV por inspeção (`/exportacao/inspecoes.csv`) não mudou (há teste que garante as mesmas colunas de antes).

## Resultado das suítes

| Suíte | Antes | Agora | Por que mudou |
|---|---|---|---|
| Backend | 334 | **348** | +14 testes em `tests/api/test_exportacao_itens.py` |
| Frontend | 124 | **125** | +1 teste (os dois links de exportação, distintos) |
| Build | ok | ok | — |
| E2E | 14 | **14** | mesmo número de passos; o passo do CSV passou a baixar também o arquivo de itens e conferir o conteúdo |

## CA → teste

| CA | Backend (`test_exportacao_itens.py`) | Frontend | E2E |
|---|---|---|---|
| CA111 | `test_cabecalhos_e_colunas_exatos` | — | download com nome `itens-checklist.csv` e cabeçalho exato |
| CA112 | `test_uma_linha_por_item_de_cada_inspecao`, `test_total_de_linhas_bate_com_os_itens_da_api`, `test_item_avulso_sai_com_origem_avulso…`, `test_inspecao_cancelada_tambem_aparece` | — | 36 linhas (6 inspeções x 6 itens, a cancelada inclusa) |
| CA113 | `test_campos_da_inspecao_repetidos…`, `test_item_critico_situacao_observacao_e_origem`, `test_qtd_de_fotos_por_item` (carga real, 9 fotos), `test_qtd_de_fotos_acompanha_envio_e_exclusao` | — | linha do item 6 da INS-003 com `REPROVADA`, `sim`, `NAO_CONFORME` e 2 fotos |
| CA114 | `test_texto_com_aspas_ponto_e_virgula_e_quebra_volta_identico`, `test_texto_que_parece_formula_e_neutralizado`, `test_numeros_e_codigos_nao_recebem_apostrofo` | — | — |
| CA115 | `test_banco_vazio_so_cabecalho`, `test_csv_por_inspecao_nao_mudou` | — | — |
| CA116 | — | `Painel › dois arquivos distintos…` | clique no botão e download |

Arquivo de exemplo gerado pelo E2E (dados fictícios): `docs/evidencias/itens-checklist-e2e.csv`.

## Um erro meu no caminho (corrigido no teste, não no código)

O teste das fotos por item usava o seed dos testes, que não cria fotos (as 9 fotos só entram pelo endpoint "carregar exemplos"). O teste passou a usar a carga real.

## Limitações

- O nome do local sai como o cadastro **atual** (igual ao CSV por inspeção), não como a cópia do fechamento.
- O CSV não traz data de preenchimento por item (isso é o `respondido_em`, adiado).
