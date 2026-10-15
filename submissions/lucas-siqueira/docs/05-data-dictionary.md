# 05 — Data Dictionary

> Fonte: Kaggle *CRM Sales Predictive Analytics* (CC0). As descrições originais vêm do `metadata.csv` do próprio dataset; as observações foram medidas pelo pipeline (`solution/src/data_processing.py`).
> Os arquivos brutos ficam em `solution/data/*.csv` e nunca são alterados. As saídas geradas ficam em `solution/data/processed/`.

## 1. Tabelas brutas

### `accounts.csv` — 85 linhas, PK `account`

| Coluna | Tipo | Descrição (metadata) | Nulos | Domínio observado | Observações |
|---|---|---|---|---|---|
| `account` | texto | Nome da empresa | 0 | 85 valores únicos | Chave primária |
| `sector` | texto | Setor | 0 | 10 setores | `technolgy` → `technology` (12 contas) |
| `year_established` | inteiro | Ano de fundação | 0 | 1979–2017 | — |
| `revenue` | decimal | Receita anual, **em milhões de US$** | 0 | 4,5–11.698 | — |
| `employees` | inteiro | Número de funcionários | 0 | 9–34.288 | — |
| `office_location` | texto | Sede | 0 | 15 países | `Philipines` → `Philippines` (1 conta) |
| `subsidiary_of` | texto | Empresa-mãe | 70 | 7 empresas-mãe | Nulo = independente. FK → `accounts.account` |

### `products.csv` — 7 linhas, PK `product`

| Coluna | Tipo | Descrição | Nulos | Domínio observado |
|---|---|---|---|---|
| `product` | texto | Nome do produto | 0 | GTX Basic, GTX Pro, GTX Plus Basic, GTX Plus Pro, MG Special, MG Advanced, GTK 500 |
| `series` | texto | Série | 0 | GTX, MG, GTK |
| `sales_price` | inteiro | Preço de venda sugerido (US$) | 0 | 55–26.768 |

### `sales_teams.csv` — 35 linhas, PK `sales_agent`

| Coluna | Tipo | Descrição | Nulos | Domínio observado |
|---|---|---|---|---|
| `sales_agent` | texto | Vendedor | 0 | 35 (5 sem nenhum deal) |
| `manager` | texto | Manager responsável | 0 | 6 |
| `regional_office` | texto | Escritório regional | 0 | Central, East, West |

### `sales_pipeline.csv` — 8.800 linhas, PK `opportunity_id`

| Coluna | Tipo | Descrição | Nulos | Domínio observado | Observações |
|---|---|---|---|---|---|
| `opportunity_id` | texto | Identificador único | 0 | 8.800 únicos, 8 caracteres | Chave primária |
| `sales_agent` | texto | Vendedor | 0 | 30 | FK → `sales_teams` |
| `product` | texto | Produto | 0 | 7 | FK → `products`. **`GTXPro` (1.480 linhas) → `GTX Pro`** |
| `account` | texto | Empresa | 1.425 | 85 | FK → `accounts`. Nulos só em deals abertos |
| `deal_stage` | texto | Estágio (Prospecting > Engaging > Won/Lost) | 0 | 4 valores | — |
| `engage_date` | data (texto ISO no bruto) | Início do estágio Engaging | 500 | 20/10/2016–27/12/2017 | Nulo = Prospecting |
| `close_date` | data (texto ISO no bruto) | Data de Won/Lost | 2.089 | 01/03/2017–31/12/2017 | Nulo = deal aberto |
| `close_value` | decimal | Receita do deal (US$) | 2.089 | Won: 38–30.288; Lost: 0 | **Desfecho.** Não é previsão de valor para deals abertos |

## 2. Tabela analítica — `data/processed/opportunities_analytic.csv`

Granularidade: **uma linha por oportunidade** (8.800 linhas, 30 colunas).

**Papéis:**
- **ID:** identificador.
- **PRE:** conhecido antes do desfecho; pode ser usado como preditor.
- **OUT:** desfecho ou informação pós-fechamento; **nunca usar como preditor**.
- **AUX:** flag de qualidade.

| Coluna | Tipo | Papel | Origem / regra | Ausentes |
|---|---|---|---|---|
| `opportunity_id` | texto | ID | pipeline | — |
| `sales_agent` | texto | PRE | pipeline | — |
| `manager` | texto | PRE | `sales_teams` via `sales_agent` | — |
| `regional_office` | texto | PRE | `sales_teams` via `sales_agent` | — |
| `product` | texto | PRE | pipeline, com grafia corrigida | — |
| `series` | texto | PRE | `products` | — |
| `sales_price` | inteiro | PRE | `products`. **Estimador de valor dos deals abertos** (ganhos fecham a 99,8% da lista) | — |
| `account` | texto | PRE | pipeline | 1.425 (só abertos) |
| `account_missing` | bool | AUX | `account` é nulo. **Não usar como preditor**: só ocorre em abertos | — |
| `sector` | texto | PRE | `accounts` | 1.425 (sem conta) |
| `year_established` | decimal | PRE | `accounts` | 1.425 |
| `account_age_years` | decimal | PRE | 2017 − `year_established` | 1.425 |
| `revenue` | decimal | PRE | `accounts`, em milhões de US$ | 1.425 |
| `revenue_band` | categoria | PRE | Quartis das 85 contas: Q1 ≤ 497; Q2 ≤ 1.224; Q3 ≤ 2.741; Q4 > 2.741 | 1.425 |
| `employees` | decimal | PRE | `accounts` | 1.425 |
| `employees_band` | categoria | PRE | Quartis das 85 contas: Q1 ≤ 1.179; Q2 ≤ 2.769; Q3 ≤ 5.595; Q4 > 5.595 | 1.425 |
| `office_location` | texto | PRE | `accounts`, com grafia corrigida | 1.425 |
| `subsidiary_of` | texto | PRE | `accounts` | Nulo = independente ou sem conta |
| `is_subsidiary` | bool (anulável) | PRE | `subsidiary_of` preenchido | 1.425 (sem conta) |
| `engage_date` | data | PRE | pipeline | 500 (Prospecting) |
| `engage_month` | texto AAAA-MM | PRE* | `engage_date`. *Distorcido por truncamento e censura; não usar como preditor* | 500 |
| `age_days_at_reference` | decimal | PRE | 31/12/2017 − `engage_date`, **só para Engaging** | Prospecting e fechados |
| `possible_duplicate` | bool | AUX | Mesmo vendedor, produto, conta e `engage_date` que outro deal (64 deals) | — |
| `deal_stage` | texto | OUT | pipeline | — |
| `is_open` | bool | OUT | Estágio Prospecting ou Engaging | — |
| `is_won` | bool (anulável) | OUT | True = Won, False = Lost, nulo = aberto. **Variável-alvo** | 2.089 (abertos) |
| `close_date` | data | OUT | pipeline | 2.089 |
| `close_value` | decimal | OUT | pipeline | 2.089 |
| `cycle_days` | decimal | OUT | `close_date` − `engage_date` (1–138 dias) | 2.089 |
| `close_to_list_ratio` | decimal | OUT | `close_value` ÷ `sales_price`, só Won (0,66–1,34) | Lost e abertos |

A lista de papéis está no código (`COLUMN_ROLES`), e um teste garante que toda coluna da tabela tem papel declarado.

## 3. Política de valores ausentes

| Campo | Regra |
|---|---|
| `account` | Mantido nulo; `account_missing` = True. Ocorre só em deals abertos |
| Atributos da conta | Nulos herdados do left join quando não há conta; não são imputados |
| `subsidiary_of` | Nulo significa empresa independente, não dado faltante; `is_subsidiary` = False |
| `engage_date` | Nulo em todo Prospecting; não é imputado (não inventamos datas) |
| `close_date` / `close_value` | Nulos em todo deal aberto; nunca são imputados nem usados como previsão |

## 4. Outras saídas do pipeline

| Arquivo | Conteúdo |
|---|---|
| `data_quality_issues.csv` | Uma linha por problema: `check`, `table`, `column`, `severity` (erro/aviso/info), `rows`, `action`, `detail` |
| `table_profile.csv` | Por coluna bruta: tipo, linhas, nulos, valores distintos, linhas duplicadas |
| `reconciliation.csv` | Contagens bruto × analítico: linhas, IDs, soma de `close_value`, deals por estágio |

## 5. Glossário

| Termo | Definição |
|---|---|
| Deal aberto | `deal_stage` ∈ {Prospecting, Engaging} |
| Deal fechado | `deal_stage` ∈ {Won, Lost} |
| Win rate | Won ÷ (Won + Lost); deals abertos nunca entram no denominador |
| Ciclo | Dias entre `engage_date` e `close_date` (só fechados) |
| Deal parado | Engaging com `age_days_at_reference` > 138, o maior ciclo já observado |
| Data de referência | 31/12/2017, a última data do CRM. Usada como "hoje" |
