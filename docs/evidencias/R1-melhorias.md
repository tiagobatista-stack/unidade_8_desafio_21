# Evidências — Rodada R1 (cartões clicáveis, editar, número do processo, novo local)

Data: 2026-10-23. Escopo e regras: `HANDOFF_CLAUDE_CODE.md` (RN35–RN38, CA74–CA85, P12–P14, seção 16).

## Resultado das suítes

| Suíte | Comando | Resultado |
|---|---|---|
| Backend | `cd backend && pytest -q` | **229 passed** (eram 201) |
| Frontend | `cd frontend && npm test -- --run` | **59 passed** (eram 37) |
| Build | `cd frontend && npm run build` | ok (tsc + vite) |
| E2E | `cd e2e && npx playwright test` | **11 passed** (eram 9); telas regravadas em `docs/evidencias/telas/` |

## CA → teste

| CA | Backend | Frontend (Vitest) | E2E (Playwright) |
|---|---|---|---|
| CA74 | `test_numero_processo.py::test_cadastro_exige_numero_do_processo[3 casos]` | `paginas.test.tsx` (Nova: aviso "Informe o número do processo") | `nova inspeção…` |
| CA75 | `::test_cadastro_grava_e_devolve…_com_trim`, `::test_numero_do_processo_limite_de_60`, `::test_texto_livre_e_aceito_e_nao_e_unico` | — | — |
| CA76 | `::test_editar_numero_do_processo[Aberta, Em andamento]`, `::test_editar_numero_vazio_ou_longo_422…`, `::test_editar_numero_em_finalizada_409` | `novas-funcoes.test.tsx` (erro 422/409 na edição) | `editar inspeção, número do processo e busca` |
| CA77 | `::test_campos_editaveis_vem_da_api_por_status[3]`, `::test_campos_editaveis_vazio_em_cancelada` | `Editar inspeção › Aberta / Em andamento / Finalizada` | idem |
| CA78 | `::test_status_repetido_une_os_grupos`, `::test_status_repetido_respeita_paginacao`, `::test_status_invalido_na_lista_422` | `paginas.test.tsx` (pendências = 1 consulta com `status` repetido) | `contadores do painel listam cada categoria` |
| CA79 | `::test_filtro_por_numero_parcial_e_sem_diferenciar_maiusculas`, `::test_filtro_trata_percentual_e_sublinhado_como_texto`, `::test_filtro_combina_com_status_e_nao_vaza_aspas` | `Lista › busca por número envia numero_processo…` | `editar inspeção…` (busca por `20005`) |
| CA80 | — (contadores: `test_api_painel.py`) | `Painel: contadores clicáveis` (links, destino, total listado = contador, canceladas fora) | `contadores do painel listam cada categoria` |
| CA81 | — | `Lista › botão Editar só aparece em inspeções editáveis`, `Editar inspeção › botão Editar no detalhe…` | `editar inspeção…` |
| CA82 | — | `Editar inspeção › salvar envia só o que mudou`, `sem alterações não chama a API`, `erro da API…` | `editar inspeção…` |
| CA83 | `::test_criar_local_novo_e_usar_na_inspecao`, `::test_local_fora_de_mt_nao_e_criado` | `Nova inspeção: novo local` (5 testes, inclui fluxo completo) | `nova inspeção e cancelamento com motivo` (fora de MT → corrige → seleciona) |
| CA84 | `unit/test_migracao.py` (3 testes: dados preservados, idempotência, inspeção antiga editável) | — | — |
| CA85 | `test_api_painel.py::test_csv_colunas_e_linhas`, `::test_csv_neutraliza_formulas` | — | `exportação CSV…` (cabeçalho com `numero_processo`) |

## Defeitos encontrados durante a rodada (todos corrigidos)

- Os testes antigos criavam inspeção sem o campo agora obrigatório e liam o CSV por posição de coluna; foram atualizados (CSV agora por nome de coluna).
- A união de duas consultas para "Pendências" no frontend foi substituída por `status` repetido na API (a paginação ficaria errada com mais de uma página).
- **Layout:** a coluna "Ações" (botão Editar) ficava fora da área visível por causa da largura da tabela. Visto na captura de tela, não pelos testes; corrigido (largura do conteúdo e quebra de linha) e regravado.
- Seletores ambíguos no E2E (o link "Editar INS-004" também contém "INS-004"); passaram a usar correspondência exata.

## Limitações desta rodada

- Número do processo sem validação de formato (decisão do usuário: texto livre) e não único.
- A lista mostra até 100 inspeções por consulta; não há paginação na tela.
- O site da Vercel **não foi reimplantado** com estas mudanças (aguarda confirmação); o backend em execução na máquina precisa ser reiniciado para ter a nova versão. O banco existente é migrado sozinho na inicialização.
