# Evidências — S1A (banco + API de locais, inspeções e itens)

Data de referência dos testes: 2026-10-23 (relógio fixo). `pytest -q` em `backend/`: **123 passed** (unit 44, service 38, api 41).

## CA → teste

| CA | Teste(s) |
|---|---|
| CA01, CA04 | `service::test_cadastro_valido`, `api::test_cadastrar_inspecao`, `api::test_codigos_consecutivos` |
| CA02 | `service::test_cadastro_sem_local_valido`, `api::test_cadastrar_sem_local` |
| CA03 | `unit::test_realizacao_futura`, `service::test_cadastro_realizacao_futura`, `api::test_cadastrar_realizacao_futura_e_anterior` |
| CA05, CA06, CA31 | `service::test_primeiro_item_inicia_inspecao`, `api::test_registrar_item_e_persistir` |
| CA07 | `service::test_item_avulso_so_na_propria_inspecao`, `api::test_item_avulso_adicionar_e_remover` |
| CA08 | `service::test_itens_de_finalizada_nao_alteraveis`, `api::test_itens_de_finalizada_imutaveis` |
| CA09 | `service::test_fechar_com_pendentes_lista_cada_item`, `api::test_fechar_bloqueado_lista_itens` |
| CA10 | `service::test_fechar_nc_sem_observacao_bloqueia`, `api::test_fechar_nc_sem_observacao` |
| CA11–CA13 | `unit::test_resultado_*`, `service::test_fechar_resultado[3]`, `api::test_fechar_fluxo_completo[3]` |
| CA14 | `service::test_fechar_resultado`, `api::test_fechar_fluxo_completo` |
| CA15, CA16 | `api::test_filtro_status`, `api::test_filtro_periodo_inclusivo` |
| CA17, CA34 | `api::test_detalhe_mostra_itens_e_duas_datas` |
| CA25, CA27 | `api::test_locais_listar_e_detalhar`, `unit::test_coordenadas_persistem_como_numero` |
| CA26 | `unit::test_coordenada_fora_de_mt`, `unit::test_latitude_fora_de_mt_rejeitada`, `api::test_local_latitude_fora_de_mt` |
| CA29, CA30 | `api::test_cadastrar_sem_agendamento`, `api::test_cadastrar_agendamento_28_10` |
| CA32 | `unit::test_realizacao_anterior_ao_agendamento`, `api::test_cadastrar_realizacao_futura_e_anterior` |
| CA33 | `service::test_editar_agendamento_so_em_aberta`, `api::test_patch_agendamento_por_status` |
| CA35–CA41 (API) | `service::test_observacoes_vistoria_*`, `api::test_observacoes_vistoria_via_api`, `service::test_fechar_sem_observacoes_vistoria_permitido` |

Não cobertos nesta sprint (dependem de sprints futuras): CA18–CA24, CA28 (S3), CA21 (indicadores, S3), CA42+ (fotos, S1B), CA41 na parte de interface e CSV.

## Validação em servidor real (SQLite em arquivo)

Com `uvicorn` em 127.0.0.1:8000 e banco novo em `backend/data/inspecoes.db`: criou-se um local e uma inspeção (6 itens), registrou-se o item 1 (inspeção foi para EM_ANDAMENTO com realização 2026-10-23), a API foi **encerrada e reiniciada**, e os dados voltaram idênticos (CA22 parcial). `POST /locais` com latitude −25 devolveu 422 `COORDENADA_FORA_DE_MT`.

## Decisões e lacunas registradas

- **Modelo de checklist** (6 itens) é criado na inicialização (idempotente), não só pelo seed — senão um banco novo gerava inspeções com 0 itens. `BANCO_JA_POVOADO` considerará apenas locais e inspeções.
- `POST /inspecoes` aceita `data_realizacao` opcional (CA03/CA32 exigem validá-la); se válida, é gravada. O handoff não diz o que fazer nesse caso.
- Limites não especificados no handoff: `observacoes` (cadastro) ≤ 2000 e `observacao` (item) ≤ 1000 caracteres.
- Código de erro para cancelar/fechar fora de status válido: `TRANSICAO_INVALIDA`; para editar inspeção terminal: `INSPECAO_IMUTAVEL`.
- Erros de validação de esquema (tipo/campo ausente) saem antes das regras de estado, então um PATCH malformado em inspeção finalizada devolve 422, não 409.
- `qtd_fotos` e fotos no detalhe ficam para a S1B.
