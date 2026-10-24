# R4 — Dados para a capa da SEMA e corpo do relatório técnico

Rodada executada em 4 sprints (S1 a S4), cada uma com parada para o usuário testar. Branch `r4-capa-sema-corpo-relatorio`, PR de revisão no GitHub (o merge é do dono do produto). Dados 100% fictícios.

**Contexto.** O sistema da SEMA-MT já gera a capa do relatório técnico (1 Interessado, 2 Assunto, 3 Caracterização do empreendimento, 4 Equipe técnica) e a lavratura dos autos. Este sistema **não gera a capa**: coleta e organiza os dados que a alimentam, para copiar sem redigitar, e gera o **corpo** do relatório a partir do item 5. (O texto original chamava a rodada de R3, nome já usado pela exportação dos itens; combinou-se R4.)

## Verificação final

| Suíte | Comando | Antes da R4 | Depois |
|---|---|---|---|
| Backend | `cd backend && pytest -q` | 348 | **457** |
| Frontend | `cd frontend && npm test -- --run` | 125 | **159** (`npm run build` ok) |
| E2E | `cd e2e && npx playwright test` | 14 | **16** |

Por sprint: S1 348→405 · S2 405→431 (e 441 com a validação em português) · S3 441→453 · S4 453→457; frontend 125→125→144→156→159; E2E 14→14→14→15→16.

## Mapa dos itens do pedido

| Item | Onde |
|---|---|
| E1 dados da inspeção | S1 — `R4-S1-modelo-de-dados.md`; RN48–RN50 |
| E2 empreendimento e responsável | S1 — idem; RN51 |
| E3 coordenadas | S2 — `R4-S2-coordenadas-e-telas.md`; RN52 |
| E4 dados para a capa e lavratura | S3 — `R4-S3-dados-capa-lavratura.md`; RN53 |
| E5 corpo do relatório | S4 — abaixo; RN54 |
| E6 telas | S2 (formulários) e S3 (página de cópia) |
| E7 legado, migração e testes | S1 (migração), todas as sprints (testes), S4 (E2E) |
| E8 commits e PR | branch, commits por assunto, PR em rascunho na S1 e pronto na S4, sem merge |

## S4 — corpo do relatório (E5) e E2E (E7)

`GET /api/v1/inspecoes/{id}/relatorio` agora devolve só o corpo:
- **Cabeçalho mínimo** (sem título de capa): `Protocolo nº ... | Inspeção INS-xxx | Ref. interna NNNN/AAAA` e, quando informado, `| Relatório SEMA nº ...`. Na prévia: `Ref. interna: sem número (prévia)`.
- **5 – Constatações:** 5.1 Relato da vistoria (data e observações da vistoria), 5.2 Checklist (a tabela atual, com os totais) e 5.3 Registro fotográfico (Foto 1, 2…, com legenda, anotação, item vinculado e data de captura).
- **6 – Providências tomadas:** texto e atos; ato sem número = "nº a definir".
- **7 – Conclusão** (resultado e regra aplicada): ativável pela opção **Incluir conclusão**, ligada por padrão (`?incluir_conclusao=false` no backend).
- **Fora do corpo:** empreendimento, equipe, interessado (vão na capa) e assinatura (a autenticação é do sistema da SEMA). As "Observações gerais" do cadastro (`observacoes`) e o Objetivo também deixaram o corpo: o Objetivo vai no bloco 2 da capa. Se alguma dessas informações precisar voltar ao corpo, é uma decisão do dono do produto (nenhum item foi mantido sem perguntar).
- Mantidos: prévia "PRÉVIA, NÃO FINALIZADO", impressão pelo navegador (A4) e rodapé com "Página X de Y" (agora `Ref. interna NNNN/AAAA · INS-xxx · Sistema fictício/simulado`).
- Na tela do detalhe: "Ref. interna (relatório)", "Relatório SEMA" (quando informado) e "Protocolo nº".

**Testes novos e alterados do corpo.** Backend: `test_relatorio.py` foi adaptado (estrutura, cabeçalho, relato, providências, `incluir_conclusao` e a garantia de que os itens 1 a 4 e a assinatura não aparecem); saíram os dois testes que conferiam o empreendimento dentro do relatório (a cópia do fechamento segue coberta em `test_copia_fechamento`, `test_r4_locais` e `test_r4_dados_capa`). Frontend: `relatorio.test.tsx` reescrito para o corpo (33 testes, incluindo a opção "Incluir conclusão" sem recarregar as fotos). Nada foi enfraquecido: o que mudou é o contrato do relatório.

**E2E completo no padrão do modelo** (`fluxo.spec.ts`, último passo): cria o Local com coordenadas em GMS, CPF e endereço de correspondência; cria a inspeção com interessado MP, assunto, 3 membros na equipe e 1 notificação sem número; responde o checklist e fecha; abre "Dados para capa e lavratura" (tudo preenchido), copia tudo e confere o texto; registra o número da notificação e o nº do relatório na SEMA depois do fechamento; gera o corpo (cabeçalho com Relatório SEMA nº, itens 5, 6 e 7, opção "Incluir conclusão") e salva o PDF em [`relatorio-corpo-R4.pdf`](relatorio-corpo-R4.pdf). Telas 41 a 46 em `docs/evidencias/telas/`. As demais telas e os PDFs `relatorio-INS-004.pdf` e `relatorio-previa-INS-005.pdf` foram regenerados com a interface atual.

## Mudanças de regra de negócio (resumo)
- Equipe técnica obrigatória para fechar.
- Depois do fechamento, só o número dos atos e o Nº do relatório na SEMA são editáveis (`atos`, `numero_relatorio_sema`), com `atualizado_em`.
- O número `NNNN/AAAA` passou a ser a **Ref. interna** na exibição.

## Migração e backup
Colunas novas nulas em `inspecao`, `local` e `proprietario` e tabelas `equipe_membro` e `ato_lavrado`, criadas na subida da API (idempotente). Antes de subir a nova versão sobre um banco existente, copie `backend/data/` (fica fora do Git; cópias `backend/data_*/` também são ignoradas). Inspeções antigas ainda não finalizadas precisam de 1 membro na equipe para fechar.

## Limitações e pendências
- A lista de assuntos e de tipos de ato está no backend (`domain/constantes.py`) e no front (`src/constantes.ts`): mudar nos dois lados.
- A área de transferência depende do navegador (HTTPS ou localhost); há plano B com `execCommand`.
- "Página X de Y" no PDF só foi conferida no Chromium (limitação anterior, mantida).
- O texto do "Copiar tudo" segue o formato do exemplo do pedido; ajustes finos de rótulo dependem de como o sistema da SEMA recebe a colagem.
- Pendências antigas seguem abertas: P10 (licença), PB2 (`respondido_em`), M0 formal e a matriz CA01–CA139 completa (S4 do MVP).

## Para revisar manualmente (checklist do PR)
1. Subir a API sobre uma cópia do seu `backend/data/` e abrir inspeções antigas (detalhe, "Dados para capa e lavratura" e relatório).
2. Cadastrar um Local com GMS, CPF/CNPJ e correspondência ("mesmo endereço" e endereço próprio).
3. Criar uma inspeção com todos os blocos, tentar fechar sem equipe (deve bloquear), fechar com equipe.
4. Em "Dados para capa e lavratura", conferir "Não informado" destacado, copiar um campo, um bloco e tudo, e colar no sistema da SEMA.
5. Registrar o número de um ato e o Nº do relatório na SEMA depois do fechamento e conferir que mais nada é editável.
6. Gerar o corpo do relatório, alternar "Incluir conclusão" e imprimir/salvar em PDF.
