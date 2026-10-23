# Evidências — S1B (API de fotos e anotações)

`pytest -q` em `backend/`: **184 passed** (inclui os 123 da S1A, sem regressão). Imagens 100% geradas por código (`tests/fixtures/imagens.py`).

| CA | Teste(s) |
|---|---|
| CA42, CA57 | `api::test_envio_jpeg_cria_registro_original_e_miniatura`, `unit::test_miniatura_ate_320_e_original_integro` |
| CA43 | `api::test_envio_png_e_webp`, `unit::test_formatos_aceitos` |
| CA44, CA45 | `api::test_gif_415_e_nada_em_disco`, `api::test_texto_renomeado_jpg_415`, `unit::test_gif_*`, `unit::test_texto_renomeado_*` |
| CA46 | `api::test_limite_de_5mb` (5.242.880 B → 201; 5.242.881 B → 413) |
| CA47 | `api::test_limite_de_20_fotos` (21ª → 409; 40 arquivos em disco) |
| CA48 | `api::test_duplicada_409_mas_outra_inspecao_aceita`, `unit::test_hash_unico_por_inspecao_*` |
| CA49 | `api::test_exif_gps_ausente_nos_arquivos_gravados[jpeg,png,webp]` (lê os arquivos gravados), `unit::test_exif_e_gps_removidos_*` |
| CA50 | `api::test_foto_em_aberta_nao_muda_status` |
| CA51 | `api::test_finalizada_e_cancelada_imutaveis_mas_consultaveis` |
| CA52, CA53 | `api::test_item_de_outra_inspecao_422`, `api::test_remover_item_avulso_mantem_foto_sem_vinculo` |
| CA54 | `api::test_legenda_limites` |
| CA55, CA73 | `api::test_excluir_remove_registro_e_arquivos_e_anotacao` |
| CA56 | `api::test_fotos_persistem_no_banco` (nova sessão) |
| CA58 | parcial: `api::test_lista_mostra_qtd_fotos_e_detalhe_traz_fotos` (3/2/2/2/0 só com o seed da S3) |
| CA59 | `api::test_fechar_sem_fotos_permitido` |
| CA60 | `api::test_verificar_fotos_*` (zero em banco limpo; acusa arquivo apagado e arquivo solto) |
| CA61–CA65 | `api::test_sem_anotacao_*`, `test_anotacao_so_espacos_422`, `test_anotacao_limites_e_trim` (nada gravado em disco/banco nos 422) |
| CA66, CA67, CA68 | `api::test_edicao_de_anotacao_*`, `test_finalizada_e_cancelada_imutaveis_*` |
| CA71 (backend), CA72 | `api::test_texto_html_e_nome_com_script_*`, `api::test_anotacao_nao_altera_resultado` |

Extras: RN28 (`test_falha_ao_gravar_registro_remove_arquivos_gravados`: falha no commit → nenhum arquivo órfão), nome com `../` nunca vira caminho (`test_nome_com_caminho_*`, `test_storage_bloqueia_caminho_fora_da_base`).

Decisões: a anotação é validada antes do arquivo (campos → arquivo → limite/duplicidade) e o estado da inspeção antes de tudo (409), conforme a ordem da seção 6. O "original" é regravado só com os pixels (sem metadados) e com a orientação EXIF aplicada; o hash de duplicidade é do arquivo enviado.
CA70 e CA69/CA71 (interface) ficam para a S2B.
