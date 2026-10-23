# Evidências — frontend (S2A/S2B), painel (S3) e E2E com Playwright

## Resultado das suítes (execução final)

| Suíte | Comando | Resultado |
|---|---|---|
| Backend | `cd backend && pytest -q` | **199 passed** |
| Frontend | `cd frontend && npm test -- --run` | **36 passed** (2 arquivos) |
| Build | `cd frontend && npm run build` | ok (tsc + vite) |
| E2E | `cd e2e && npx playwright test` | **9 passed** (Chromium, API e Vite reais, banco SQLite temporário, relógio fixo em 2026-10-23) |

## Telas geradas pelo Playwright (`docs/evidencias/telas/`)

Geradas automaticamente a cada execução do E2E, na ordem do fluxo: painel vazio → confirmação de carga de exemplos → painel 5/2/3 → lista → filtro de período → pendências → nova inspeção (campos obrigatórios e preenchida) → detalhe aberta → cancelamento (modal e resultado) → bloqueio P1 (agendada para 28/10/2026) → detalhe em andamento com fotos → modal de fechar → fechamento bloqueado com itens destacados → fotos pendentes (Enviar desabilitado) → falha parcial com anotação preservada → visualizador com texto literal → galeria após recarregar → checklist respondido e observações → inspeção finalizada (somente leitura) → painel 5/1/4 → detalhe em layout de celular.
O CSV exportado no E2E fica em `docs/evidencias/exportacao-e2e.csv`.

## O que o E2E comprova no sistema real

- Banco novo → "Carregar exemplos" → indicadores 5 / 2 / 3 (CA18); segunda carga não é feita pela UI, mas a API devolve 409 nos testes de API.
- Fechar INS-004 move para 5 / 1 / 4 sem recarregar a página (CA19); a inspeção cancelada não entra em "Inspeções" nem em "Pendências" (CA20).
- Filtros de status e período (inclusivo) e "Ver pendências" (CA15, CA16).
- Fechamento com itens não respondidos mostra um destaque por item (CA09); P1 mostra a mensagem da API (CA32).
- Foto sem anotação mantém "Enviar" desabilitado (CA69); falha parcial grava as válidas e preserva a anotação da que falhou (CA70); `<b>` na anotação aparece como texto (CA71); fotos persistem após recarregar (CA56).
- Finalizada/cancelada ficam sem controles de edição (CA08, CA51).
- CSV exportado com as colunas definidas, quebras de linha entre aspas e `qtd_fotos` correto (CA23, CA28); `verificar-fotos` sem inconsistências (CA60).

## Limitações e lacunas conhecidas (não validadas ou aceitas)

- O travessão "—" do texto "FOTO FICTÍCIA — INS-00X #n" não é desenhado nas fotos de exemplo (a fonte padrão do Pillow não tem o glifo); o texto da anotação não é afetado.
- CA22 (persistência após reiniciar) foi validado manualmente em S1A (API reiniciada em servidor real); o E2E recarrega a página, mas não reinicia a API.
- Não há teste automatizado de acessibilidade, de navegadores além do Chromium nem de carga. O E2E não roda no CI (exige navegador).
- Código de erro de status de transição e limites de `observacoes` (2000) e `observacao` de item (1000) foram decisões minhas, registradas em `S1A.md`.
