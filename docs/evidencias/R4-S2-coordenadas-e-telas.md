# R4 · Sprint S2 — coordenadas em GMS e telas (E3 e E6)

Branch `r4-capa-sema-corpo-relatorio`. Dados 100% fictícios.

## Verificação

| Suíte | Comando | Antes (S1) | Depois (S2) |
|---|---|---|---|
| Backend | `cd backend && pytest -q` | 405 | **431** |
| Frontend | `cd frontend && npm test -- --run` | 125 | **144** (`npm run build` ok) |
| E2E | `cd e2e && npx playwright test` | 14 | **14** |

## E3 — coordenadas

**Backend** (regra e conversão só no serviço/domínio, `domain/coordenadas.py`)
- Exibição: `LAT 11° 46' 34" S | LONG 59° 05' 12" W` (só o hemisfério, sem sinal). Os segundos são arredondados sobre o **total de segundos**, então nunca sai 60" (59,9996" vira o minuto seguinte, e 59' 59,9996" vira o grau seguinte).
- Digitação: `LocalIn` aceita `latitude`/`longitude` (decimal) **ou** `latitude_gms`/`longitude_gms` (texto). Havendo os dois no mesmo eixo, o GMS vale. A conversão para decimal (5 casas, como o banco) ocorre ao salvar; depois valem os limites de MT de sempre (`COORDENADA_FORA_DE_MT`).
- Validação do GMS (422, campo `latitude_gms`/`longitude_gms`): formato, hemisfério coerente com o eixo (N/S na latitude, E/W/O na longitude), **minutos e segundos < 60**, graus dentro de 0–90/0–180. Aceita `11 46 34 S`, `11º46'34"S`, `11° 46′ 34″ s`, segundos com vírgula decimal.
- Saída (`LocalOut` e `Empreendimento`): `latitude_gms`, `longitude_gms` e `coordenadas_gms`.

**Frontend**
- Seletor "Decimal" / "Graus, minutos e segundos (GMS)" na tela de Locais. A máscara completa os símbolos enquanto se digita (`__° __' __" S` e `___° __' __" W`); só o modo escolhido vai no corpo. Na edição os dois formatos já vêm preenchidos pela API (o front não converte nada).

**Testes pedidos** (`tests/unit/test_coordenadas_gms.py`, `tests/api/test_r4_coordenadas.py`): o exemplo nos dois sentidos (GMS→decimal→GMS e decimal→GMS), borda de arredondamento (59,9996" e varredura de 730 valores sem 60), entrada inválida (minutos = 60, segundos = 60, hemisfério errado, formato inválido, fora de MT, coordenada ausente).

## E6 — telas
- **Nova inspeção** e **Editar inspeção**: blocos Interessado, Assunto (lista + "Outro" com texto livre), Equipe técnica (adicionar/remover membros) e Providências tomadas (texto + atos com tipo e número). A Edição acrescenta "Nº do relatório na SEMA". Componente comum: `components/BlocosCapa.tsx`.
- **Finalizada**: o detalhe mostra "Registrar números da SEMA" (quando a API libera `campos_editaveis`); a edição deixa só o número dos atos e o nº SEMA editáveis (tipo fixo, sem adicionar/remover) e o resto em leitura, com a regra decidida pela API.
- **Locais**: "Nome fantasia / denominação"; endereço do empreendimento (logradouro, município, UF com padrão MT, CEP com máscara); coordenadas com GMS; por responsável "Nome / Razão social", CPF/CNPJ com máscara, telefone e endereço para correspondência, com o atalho "Mesmo endereço do empreendimento" (envia a flag; a API copia logradouro, município, UF e CEP).
- `id`, `name` e `label` em todos os campos novos (o teste genérico de rótulos segue passando).

## Testes alterados (e por quê)
- `locais.test.tsx` e `novas-funcoes.test.tsx`: o corpo do cadastro de Local agora inclui `uf: "MT"` (UF padrão pré-preenchida). Nada foi enfraquecido.
- `tests/ajuda.tsx`: `campos_editaveis` simulados incluem os campos da capa (espelha a API).

Testes novos do front: `tests/r4-s2.test.tsx` (19).

## Limitações e próximos passos
- A lista de assuntos e de tipos de ato está duplicada no front (`src/constantes.ts`) só para montar os seletores; a API valida os valores. Se a lista mudar, atualizar os dois lados.
- Não houve conferência visual do layout dos formulários novos nesta sprint (as capturas de tela entram na S4); vale olhar Locais e Nova inspeção no navegador, inclusive em tela estreita.
- A exibição dos dados da capa (página "Dados para a capa e lavratura") é a S3.
