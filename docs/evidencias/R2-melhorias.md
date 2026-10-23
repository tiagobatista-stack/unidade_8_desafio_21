# Evidências — Rodada R2 (usabilidade, empreendimento, cópia no fechamento e relatório)

Data: 2026-10-23. Escopo e regras: `HANDOFF_CLAUDE_CODE.md` (RN39–RN46, CA86–CA110, P15–P17, PB1–PB3, seção 16).

## Resultado das suítes (execução final, antes do commit de documentação)

| Suíte | Comando | Antes da R2 | Agora | Por que mudou |
|---|---|---|---|---|
| Backend | `cd backend && pytest -q` | 229 | **334** | +105 testes: orientações A1/A3 (11), CAR, telefone, Locais e migração do C1 (43), cópia e legado do C2 (13), relatório, numeração e legado da numeração do C3 (33), fotos de exemplo (5) |
| Frontend | `cd frontend && npm test -- --run` | 59 | **124** | +65 testes: correções A1–A5 e a11y genérica (18), Locais e empreendimento (13), origem da cópia (4), relatório e impressão (30) |
| Build | `cd frontend && npm run build` | ok | ok | — |
| E2E | `cd e2e && npx playwright test` | 11 | **14** | +3 passos: Locais com CAR e proprietários, cópia no fechamento, relatório com PDF; o passo do bloqueio P1 foi reescrito (agora o aviso e os seletores desabilitados) |

Nenhum teste existente foi relaxado. Os testes que mudaram só refletem contrato novo: `numero_processo` obrigatório (R1), coluna do CSV, rótulos das datas, `preencher_legado` devolvendo também `numeros`, corpo do `POST /locais` com `numero_car` e `proprietarios`.

## CA → teste

| CA | Backend | Frontend (Vitest) | E2E / evidência |
|---|---|---|---|
| CA86 | `test_orientacoes.py::test_fechar_aberta_devolve_orientacao_com_codigo_estavel`, `test_detalhe_informa_motivo_de_fechamento_bloqueado` | `correcoes-a › A1` (botão desabilitado + motivo + descrição acessível) | tela `25-aviso-agendamento-futuro-e-fechar-desabilitado` |
| CA87 | — | `correcoes-a › A2` | idem |
| CA88 | `test_orientacoes.py::test_detalhe_aviso_preventivo…`, `test_aviso_acompanha_o_relogio_injetavel`, `test_bloqueio_da_api_continua_valendo…` | `correcoes-a › A3` (alerta, link, selects desabilitados, some ao reagendar) | passo "INS-005: agendamento futuro…" |
| CA89 | — | `correcoes-a › A4` (verificação genérica em Nova, Lista, Editar, Detalhe, fotos, visualizador, modais, Locais) | mutação conferida (remover um `name` faz o teste falhar) |
| CA90 | — | `correcoes-a › A5` | passo "responder itens… fechar" (`Checklist concluído em …`) |
| CA91 | `test_contato.py` (CAR), `test_locais_empreendimento.py::test_car_*` | `locais › aviso suave do CAR` | passo "Locais: cadastrar e editar…" |
| CA92 | `test_contato.py` (telefone), `test_locais_empreendimento.py::test_erros_de_proprietarios_apontam_a_linha`, `test_limite_de_20_proprietarios` | `locais › Cadastrar local` | idem |
| CA93 | `test_locais_empreendimento.py::test_put_*` | `locais › Editar local` | idem |
| CA94 | — | `locais › Tela Locais`, `Cadastrar local`, `Editar local` | telas `14` a `18` |
| CA95 | `test_listagem_e_detalhe_da_inspecao_trazem_os_dados` | `locais › Detalhe da inspeção: Empreendimento` | tela `18-detalhe-empreendimento-car-e-proprietarios` |
| CA96 | `test_copia_fechamento.py::test_fechar_grava_copia…`, `test_cada_campo_da_copia_e_preservado`, `test_antes_do_fechamento_usa_os_dados_atuais…`, `test_outra_inspecao_aberta…` | `locais › origem dos dados do empreendimento` | passo "cópia no fechamento…" (tela `36`) |
| CA97 | `test_falha_ao_copiar_desfaz_o_fechamento` | — | — |
| CA98 | `test_legado_copia.py` (4 testes) | — | — |
| CA99 | `test_relatorio.py::test_seed_ja_vem_numerado…`, `test_numeros_sequenciais_e_sem_repeticao`, `test_indice_unico_impede_numero_repetido` | `relatorio › título numerado` | PDF `relatorio-INS-004.pdf` |
| CA100 | `test_relatorio.py::test_virada_de_ano_reinicia_a_sequencia_e_nao_reutiliza` | — | — |
| CA101 | `test_cancelar_ou_fechamento_bloqueado_nao_consomem_numero`, `test_gerar_a_previa_nao_consome_numero` | — | — |
| CA102 | `test_relatorio_finalizado_traz_as_seis_secoes_na_ordem`, `test_checklist_numerado_com_totais…` | `relatorio › 6 seções`, `checklist numerado…` | telas `37`, `38` |
| CA103 | `test_fotos_numeradas_com_original_e_item_vinculado` | `relatorio › fotos numeradas…`, `agrupadas em pares` | PDF (2 fotos por página) |
| CA104 | `test_conclusao_traz_o_resultado_e_a_regra[4]`, `test_dominio_relatorio.py` | `relatorio › conclusão` | PDF |
| CA105 | `test_previa_*` | `relatorio › Relatório em prévia` | tela `39` e `relatorio-previa-INS-005.pdf` |
| CA106 | — | `relatorio › CSS de impressão…`, `rodapé de todas as páginas vem da regra @page`, `prévia repete a marca no topo` | **PDFs conferidos página a página** |
| CA107 | — | `relatorio › com fotos, a impressão só é liberada…` | passo do relatório (botão habilitado após carregar) |
| CA108 | `test_seed_so_tem_dados_ficticios` | — | revisão dos arquivos staged e das telas |
| CA109 | `test_migracao.py` (7 testes), `test_legado_copia.py::test_banco_antigo_ganha_coluna_e_indice_unico…` | — | — |
| CA110 | `test_fotos_exemplo.py` | — | PDF (foto "FOTO FICTÍCIA — INS-004 #1") |

## Defeitos encontrados durante a rodada (todos corrigidos)

1. **Autoflush no fechamento:** reservar o número do relatório consultava o banco enquanto a inspeção estava pela metade (resultado preenchido, status ainda não) e o CHECK recusava. Cópia e número passaram a ser reservados antes de alterar os campos de fechamento, tudo no mesmo commit.
2. **Rodapé do relatório cobrindo conteúdo no PDF:** com `position: fixed` o rodapé apareceu no topo das páginas 2 a 5, em cima de linhas da tabela e do "Resultado". Visto abrindo o PDF gerado, não pelos testes de DOM. Passou para as caixas de margem do `@page` (injetadas pela página), que repetem em todas as páginas.
3. **Tabela do checklist quebrada entre páginas** deixando linhas órfãs; o bloco agora não se parte.
4. **Botão "Gerar relatório" só aparecia em inspeção editável** (ficava dentro do bloco de ações); a finalizada ficava sem ele. Corrigido e coberto por teste nos quatro status.
5. **Fotos de exemplo com quadrados** no "Í" e no "—" (fonte padrão do Pillow); agora usa uma fonte TrueType do sistema, com fallback ASCII.
6. **Contradição de escopo no handoff** (RN36/P13/seção 13 diziam que editar local estava fora do escopo, mas a tela Locais edita); corrigida.
7. Erros dos meus próprios testes: regex ampla demais no teste da prévia (casava o número do processo), índice errado num teste de ordem das seções e seletores ambíguos no E2E. Corrigidos nos testes, sem alterar comportamento.

## Verificação de impressão (PDF gerado pelo Chromium via Playwright)

- `relatorio-INS-004.pdf` (5 páginas): identificação, empreendimento (cópia do fechamento) e objetivo na página 1; checklist na 2; fotos 1 e 2 na 3; fotos 3 e 4 na 4; conclusão na 5. Rodapé "Relatório nº 0004/2026 · INS-004 · Sistema fictício/simulado" e "Página X de 5" em todas.
- `relatorio-previa-INS-005.pdf` (2 páginas): "PRÉVIA, NÃO FINALIZADO" no topo de cada página, marca diagonal na primeira, título "(sem número)" e rodapé "Relatório sem número (prévia)".

## Limitações desta rodada

- "Página X de Y" foi verificado só no Chromium. O Firefox pode imprimir sem essa numeração.
- Para finalizadas anteriores à cópia, o preenchimento do legado usa o Local de hoje (não é possível reconstituir o do fechamento).
- Lista de inspeções e CSV continuam mostrando o nome do local atual, não a cópia.
- O número de relatório é reservado pelo UPDATE do contador dentro da transação; a segunda barreira é o índice único. Não foi feito teste com fechamentos realmente simultâneos (uso é de um único usuário).
- Parte B não implementada (aguarda decisão): ver PB1 a PB3 no handoff.
