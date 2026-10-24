# R4 · Sprint S3 — página "Dados para a capa e lavratura" (E4)

Branch `r4-capa-sema-corpo-relatorio`. Dados 100% fictícios. Captura: `docs/evidencias/telas/41-dados-capa-e-lavratura.png`.

## Verificação

| Suíte | Comando | Antes (S2) | Depois (S3) |
|---|---|---|---|
| Backend | `cd backend && pytest -q` | 441 | **453** |
| Frontend | `cd frontend && npm test -- --run` | 144 | **156** (`npm run build` ok) |
| E2E | `cd e2e && npx playwright test` | 14 | **15** |

## O que foi feito

**Backend** — `GET /api/v1/inspecoes/{id}/dados-capa` (`services/capa_service.py`, `schemas/capa.py`). A regra de montagem fica no backend; a tela só renderiza.
- Blocos na ordem da capa: **1 – Interessado**, **2 – Assunto** (com o Objetivo), **3 – Caracterização do empreendimento** (nome fantasia, responsáveis com nome/razão social e CPF/CNPJ, CAR, coordenadas em GMS, endereço e CEP), **4 – Equipe técnica**, mais **Atos a lavrar** (cada ato com tipo e número ou "nº a definir", protocolo, empreendimento, coordenadas, CAR e, por responsável, nome/razão social, CPF/CNPJ, telefone e endereço para correspondência).
- Cada bloco traz o `texto` pronto, no formato do modelo, e a resposta traz o `texto_completo` (blocos separados por linha em branco) e `campos_faltando`.
- Cada campo traz `valor` (ou "Não informado"), `copiar` (vazio se não há valor), `ausente` e `faltando`. **Faltando** = vazio e necessário para a SEMA (destacado); campo **opcional** vazio (Comarca) é só `ausente` (esmaecido, sem alerta e sem linha no texto). Interessado totalmente vazio vira "Demanda interna / de ofício" e nada é marcado como faltando nele.
- Finalizada usa a cópia do empreendimento gravada no fechamento; as demais, os dados atuais do Local (mesma regra do detalhe).

**Frontend** — `pages/CapaPage.tsx`, rota `/inspecoes/:id/capa`, botão "Dados para capa e lavratura" no detalhe (qualquer status).
- Botão **Copiar** em cada campo (desabilitado quando não há valor), **Copiar bloco** e **Copiar tudo**; confirmação "Copiado: …" e aviso quando a cópia falha. Sem a API moderna da área de transferência há um plano B (`utils/copiar.ts`).
- Campos faltando em destaque (cor, borda lateral e negrito, além do texto "Não informado") e um resumo no topo com a contagem e os links para Editar inspeção e Locais.

## Testes
- Backend (`tests/api/test_r4_dados_capa.py`, 12): o texto do "Copiar tudo" de INS-001 e INS-003 do seed **bate exatamente** com o esperado; ordem dos blocos; exemplo do modelo para o bloco Interessado (MP, comarca de Juína); "Não informado" e `faltando`; comarca opcional; interessado parcial; demanda interna; assunto "Outro"; número do ato registrado depois do fechamento aparece; finalizada usa a cópia; inspeção sem nada novo não quebra; 404.
- Frontend (`tests/r4-s3.test.tsx`, 12): blocos e campos, destaque e contagem, campo opcional, botão desabilitado, cópia de campo, de bloco e de tudo (conteúdo lido da área de transferência), falha de cópia, tudo preenchido, singular, erro da API e link no detalhe.
- E2E (1 novo, no fim do fluxo para não renumerar as capturas): abre INS-001, confere os cinco blocos e os 2 campos faltando, copia tudo e compara com o texto da API. No Windows a área de transferência devolve CRLF; o teste normaliza as quebras antes de comparar.

## Limitações e próximos passos
- Os exemplos de texto usam o protocolo do seed (`SEMA-PRO-2026/10001`); o exemplo do enunciado (`212345/2030`) é coberto por um teste que edita o protocolo.
- As capturas antigas (telas 01–40) e os PDFs não foram regenerados nesta sprint; isso é feito na S4 com a documentação.
- O corpo do relatório (itens 5 a 7) é a S4.
