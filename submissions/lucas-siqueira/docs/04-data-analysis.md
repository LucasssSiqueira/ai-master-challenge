# 04 — Data Analysis: CRM Sales Pipeline

> Etapa 02 — Data Exploration & Engineering. Todos os números deste documento são reproduzíveis:
>
> ```bash
> cd solution
> python -m src.data_processing        # tabela analítica + log de qualidade em data/processed/
> python -m src.exploratory_analysis   # todas as tabelas abaixo
> python -m pytest tests/test_data_processing.py
> ```

## Resumo: as 5 descobertas mais relevantes para o negócio

| # | Descoberta | Evidência | Implicação |
|---|---|---|---|
| 1 | **81% dos deals em Engaging estão parados além de qualquer ciclo já observado.** | 1.291 de 1.589 deals em Engaging têm mais de 138 dias em 31/12/2017; nenhum deal fechado levou mais de 138 dias. Idade mediana: 165 dias. | O maior ganho imediato é limpar o pipeline (requalificar ou encerrar), não priorizar melhor. O forecast baseado nesse pipeline está inflado. |
| 2 | **Nenhum atributo do CRM está associado à conversão.** | A taxa de vitória varia só de 60% a 66% entre produtos, setores, regiões, managers e portes. Em teste temporal, todas as variáveis ficam com AUC entre 0,47 e 0,52 (0,50 = acaso). Os qui-quadrados por permutação têm p entre 0,10 e 0,97, e V de Cramér ≤ 0,07. | Um modelo preditivo com esses dados venderia ruído. A priorização deve se basear em valor e tempo, e a "chance" deve ser só informativa. |
| 3 | **A diferença entre vendedores é compatível com acaso.** | A taxa de vitória vai de 55% a 70%, mas o desvio-padrão observado (0,037) é quase igual ao esperado só por amostragem (0,033). Para 28 dos 30 vendedores, o intervalo de 95% contém a média do time. | Rankings de desempenho individual baseados em win rate são enganosos. Não se deve cobrar nem premiar vendedores por essa métrica sem mais dados. |
| 4 | **O valor do deal é previsível; o resultado não.** | Ganhos fecham a 99,8% do preço de lista (mediana), e o preço varia 487× entre produtos (US$ 55 a US$ 26.768). | O preço de lista é o melhor estimador de valor de um deal aberto. `close_value` não pode ser usado: é desfecho e é nulo nos abertos. |
| 5 | **Os dados têm vieses de seleção que distorcem análises ingênuas.** | Nenhum fechamento antes de 01/03/2017, apesar de engajamentos desde 20/10/2016: deals engajados em 2016 têm taxa de vitória de 81–82%, porque os que perderam cedo não estão no dataset. Conta ausente aparece em 1.425 deals abertos e em 0 fechados. | Variáveis como mês de engajamento ou "tem conta" parecem preditivas, mas são artefatos de coleta. Também há um padrão trimestral improvável e datas uniformes inclusive em fins de semana (H: dataset sintético). |

---

## 1. Metodologia

1. **Fonte:** dataset Kaggle *CRM Sales Predictive Analytics* (`agungpambudi/crm-sales-predictive-analytics`, licença CC0), baixado em 15/10/2026 pela API pública do Kaggle. Os quatro arquivos esperados existem: `accounts.csv`, `products.csv`, `sales_teams.csv` e `sales_pipeline.csv`, além de `metadata.csv` (descrição das colunas). Nenhum dado foi inventado.
2. **Pipeline** (`solution/src/data_processing.py`):
   1. Lê os CSVs.
   2. Valida as chaves primárias.
   3. Padroniza grafias.
   4. Valida as chaves estrangeiras e as regras de negócio.
   5. Faz os joins com `validate="many_to_one"`.
   6. Reconcilia as contagens.
   7. Grava a tabela analítica e o log de qualidade em `data/processed/`.

   Qualquer erro interrompe a execução. Os arquivos brutos nunca são alterados (há teste com hash SHA-256).
3. **Análises** (`solution/src/exploratory_analysis.py`):
   - Conversão calculada só sobre deals fechados (Won + Lost = 6.711), com intervalo de confiança de Wilson de 95%.
   - Associação medida por qui-quadrado com p-valor por permutação (2.000 permutações) e V de Cramér.
   - Poder preditivo medido por AUC em **holdout temporal**: treino com fechados até 30/09/2017 (n = 4.726) e teste com fechados depois (n = 1.985). Variáveis categóricas viram win rate histórico com *shrinkage* bayesiano (k = 50).
   - Tempo no pipeline avaliado também em **snapshots point-in-time**: no fim de cada mês, só os deals abertos naquele dia.
4. **Convenção:** **[FATO]** é um número medido no dado; **[H]** é uma hipótese ou interpretação.

---

## 2. Volume, estrutura e tipos

| Tabela | Linhas | Colunas | Chave primária | Observações |
|---|---|---|---|---|
| `accounts` | 85 | 7 | `account` | `revenue` em milhões de US$; `subsidiary_of` nulo em 70 (= empresa independente) |
| `products` | 7 | 3 | `product` | 3 séries (GTX, MG, GTK); preço de US$ 55 a US$ 26.768 |
| `sales_teams` | 35 | 3 | `sales_agent` | 6 managers, 3 escritórios (Central, East, West) |
| `sales_pipeline` | 8.800 | 8 | `opportunity_id` | Tabela fato; IDs de 8 caracteres, todos únicos |

Tipos: as chaves e categorias são texto; `year_established`, `employees` e `sales_price` são inteiros; `revenue` e `close_value` são decimais; `engage_date` e `close_date` vêm como texto ISO e são convertidas para data no pipeline (falha se alguma não for parseável).

Períodos **[FATO]**: `engage_date` vai de 20/10/2016 a 27/12/2017; `close_date`, de 01/03/2017 a 31/12/2017.

---

## 3. Chaves e relacionamentos

```
accounts (85) 1 ──< N sales_pipeline (8.800) >── 1 products (7)
                          │
                          N
                          └──> 1 sales_teams (35)
accounts.subsidiary_of ──> accounts.account (autorrelacionamento)
```

| Relacionamento | Cardinalidade | Resultado da validação |
|---|---|---|
| `sales_pipeline.product` → `products.product` | N:1 | **1.480 órfãos no bruto** (`GTXPro` ≠ `GTX Pro`); 0 após a correção |
| `sales_pipeline.sales_agent` → `sales_teams.sales_agent` | N:1 | 0 órfãos; 5 vendedores do cadastro sem nenhum deal |
| `sales_pipeline.account` → `accounts.account` | N:1 (opcional) | 0 órfãos entre os 7.375 preenchidos; 1.425 nulos |
| `accounts.subsidiary_of` → `accounts.account` | N:1 (opcional) | 0 órfãos; 15 subsidiárias de 7 empresas-mãe |

Os joins usam `validate="many_to_one"`, e a reconciliação confirma que não houve perda nem duplicação.

| Reconciliação | Bruto | Analítico |
|---|---|---|
| Linhas | 8.800 | 8.800 |
| `opportunity_id` distintos | 8.800 | 8.800 |
| Soma de `close_value` | 10.005.534 | 10.005.534 |
| Won / Lost / Engaging / Prospecting | 4.238 / 2.473 / 1.589 / 500 | idem |

---

## 4. Qualidade dos dados

### 4.1 Nulos

| Coluna | Nulos | Diagnóstico | Tratamento |
|---|---|---|---|
| `sales_pipeline.account` | 1.425 (16,2%) | **Todos em deals abertos**: 1.088 Engaging e 337 Prospecting; 0 fechados | Mantido nulo + flag `account_missing` |
| `sales_pipeline.engage_date` | 500 | Exatamente os 500 Prospecting (esperado) | Mantido nulo; idade não calculável |
| `sales_pipeline.close_date` / `close_value` | 2.089 | Exatamente os 2.089 abertos (esperado) | Mantido nulo; nunca imputado |
| `accounts.subsidiary_of` | 70 | Empresa sem controladora, não é dado faltante | `is_subsidiary` = False |

### 4.2 Duplicidades

- **[FATO]** Não há linhas duplicadas em nenhuma tabela, nem chaves primárias repetidas.
- **[FATO]** 64 deals (32 pares) têm mesmo vendedor, produto, conta e data de engajamento, com IDs diferentes: 32 Lost, 19 Won, 10 Prospecting e 3 Engaging.
- **[H]** Podem ser duplicatas de digitação ou vendas legítimas de várias unidades. Foram mantidos e marcados com `possible_duplicate`.

### 4.3 Inconsistências

| Problema | Linhas | Tratamento |
|---|---|---|
| `GTXPro` no pipeline vs `GTX Pro` no catálogo | 1.480 deals | Corrigido. Sem a correção, 17% dos deals ficariam sem preço |
| Setor `technolgy` | 12 contas | Corrigido para `technology` |
| País `Philipines` | 1 conta | Corrigido para `Philippines` |
| Vendedores sem deals (Carl Lin, Carol Thompson, Elizabeth Anderson, Mei-Mei Johns, Natalya Ivanova) | 5 | Mantidos no cadastro; ausentes da tabela analítica |

### 4.4 Regras de negócio verificadas (todas com 0 violações)

- Won com `close_value` > 0, e Lost com `close_value` = 0.
- Deals abertos sem data ou valor de fechamento, e deals fechados com os dois.
- `close_date` ≥ `engage_date`. Nenhum deal fecha no mesmo dia em que é engajado: o ciclo mínimo é 1 dia.
- Prospecting sem `engage_date`, e os demais estágios com essa data.

O log completo fica em `data/processed/data_quality_issues.csv`.

---

## 5. Distribuição dos estágios

| Estágio | Deals | % |
|---|---|---|
| Won | 4.238 | 48,2% |
| Lost | 2.473 | 28,1% |
| Engaging | 1.589 | 18,1% |
| Prospecting | 500 | 5,7% |

- **[FATO]** Win rate global (Won ÷ fechados) = **63,15%** (4.238 / 6.711).
- **[FATO]** O pipeline aberto tem 2.089 deals: 1.589 Engaging e 500 Prospecting.

---

## 6. Padrões de conversão (somente deals fechados, IC 95% de Wilson)

### 6.1 Produto

| Produto | Preço | Fechados | Win rate | IC 95% |
|---|---|---|---|---|
| GTK 500 | 26.768 | 25 | 60,0% | 40,7–76,6% |
| MG Advanced | 3.393 | 1.084 | 60,3% | 57,4–63,2% |
| GTX Plus Basic | 1.096 | 1.051 | 62,1% | 59,2–65,0% |
| GTX Pro | 4.821 | 1.147 | 63,6% | 60,7–66,3% |
| GTX Basic | 550 | 1.436 | 63,7% | 61,2–66,2% |
| GTX Plus Pro | 5.482 | 745 | 64,3% | 60,8–67,7% |
| MG Special | 55 | 1.223 | 64,8% | 62,1–67,5% |

Os intervalos se sobrepõem, e o preço não se relaciona com a conversão.

### 6.2 Setor

A taxa de vitória vai de 61,2% (finance) a 64,8% (marketing), e todos os intervalos se sobrepõem. Qui-quadrado: p = 0,97.

### 6.3 Vendedor

- **[FATO]** 30 vendedores com deals fechados. A taxa de vitória vai de 55,0% (Lajuana Vencill, n = 231) a 70,4% (Hayden Neloms, n = 152).
- **[FATO]** O desvio-padrão entre vendedores é de 0,037. Só pela amostragem (n mediano de 220), o esperado seria 0,033.
- **[FATO]** O intervalo de 95% contém a média do time para 28 de 30 vendedores. Qui-quadrado: p = 0,27; V de Cramér = 0,07.

### 6.4 Porte da empresa (quartis calculados sobre as 85 contas)

| Faixa | Receita (US$ mi) | Win rate | Faixa | Funcionários | Win rate |
|---|---|---|---|---|---|
| Q1 | 4,5–497 | 64,1% | Q1 | 9–1.179 | 64,0% |
| Q2 | 497–1.224 | 61,3% | Q2 | 1.179–2.769 | 61,2% |
| Q3 | 1.224–2.741 | 64,9% | Q3 | 2.769–5.595 | 65,1% |
| Q4 | 2.741–11.698 | 62,4% | Q4 | 5.595–34.288 | 62,5% |

Não há tendência monótona. Qui-quadrado: p = 0,13 (receita) e p = 0,10 (funcionários).

### 6.5 Teste de associação consolidado

| Variável | Categorias | Qui² | p (permutação) | V de Cramér |
|---|---|---|---|---|
| product | 7 | 6,5 | 0,36 | 0,031 |
| sector | 10 | 2,8 | 0,97 | 0,021 |
| regional_office | 3 | 1,0 | 0,62 | 0,012 |
| manager | 6 | 2,4 | 0,79 | 0,019 |
| sales_agent | 30 | 33,3 | 0,27 | 0,070 |
| revenue_band | 4 | 5,4 | 0,13 | 0,028 |
| employees_band | 4 | 6,2 | 0,10 | 0,030 |
| is_subsidiary | 2 | 0,1 | 0,74 | 0,004 |
| office_location | 15 | 14,4 | 0,44 | 0,046 |

Nenhuma variável tem associação estatisticamente significativa (todas com p > 0,05), e todas as associações são desprezíveis (V < 0,1).

---

## 7. Tempo no pipeline

| | Fechados | p25 | Mediana | p75 | p95 | Máx |
|---|---|---|---|---|---|---|
| Won (dias engage→close) | 4.238 | 9 | 57 | 88 | 116 | 138 |
| Lost | 2.473 | 7 | 14 | 79 | — | 138 |

- **[FATO]** 50,5% dos Lost fecham em até 14 dias. Perder rápido é o padrão; ganhar leva mais tempo.
- **[FATO]** Deals em Engaging em 31/12/2017: idade mediana de 165 dias, máximo de 423. **1.291 (81,2%) passam de 138 dias**, o maior ciclo já observado.
- **[FATO]** Prospecting não tem nenhuma data. A idade desses deals não é mensurável, e não foi inventada.

### O tempo prevê o resultado?

- **Visão ingênua (com vazamento):** a taxa de vitória por ciclo total vai de 53,5% (até 7 dias) a 75,6% (120–138 dias). Mas o ciclo total só é conhecido **depois** do fechamento.
- **Visão correta (point-in-time):** nos 9 snapshots mensais de 2017, a idade dos deals abertos naquela data tem AUC entre 0,46 e 0,57, com média ≈ 0,51.
- **Probabilidade condicional:** a taxa de vitória de um deal que já sobreviveu *a* dias sobe de 63% (a = 0) para 69% (a > 14) e 76% (a > 120). O ganho é real, mas pequeno, e a ordem entre deals mal muda.

**[H]** O tempo serve mais para identificar deals parados e o momento de agir do que para prever o resultado.

---

## 8. Variáveis candidatas ao scoring

Poder preditivo em holdout temporal (AUC; 0,50 = acaso):

| Variável | AUC teste | Decisão | Justificativa |
|---|---|---|---|
| `sales_agent` | 0,522 | Informativa (peso 0) | Melhor da lista, mas sem significância (p = 0,27) |
| `office_location` | 0,518 | Não usar | 15 países, 83% dos deals nos EUA; ausente em 68% dos abertos |
| `employees_band` | 0,519 | Não usar | p = 0,10; ausente em 68% dos abertos |
| `regional_office` / `product` / `series` | 0,50 | Não usar como chance | Sem sinal |
| `manager` / `account` / `sector` / `revenue_band` | 0,48–0,49 | Não usar | Sem sinal; conta ausente em 68% dos abertos |
| `sales_price` | 0,495 | **Usar como valor**, não como chance | Não prevê o resultado, mas define quanto vale ganhar (fecha a 99,8% da lista) |
| `age_days_at_reference` | ≈ 0,51 (snapshots) | **Usar como urgência e estagnação** | Não prevê o resultado, mas separa deals parados (> 138 dias) e a janela típica (9–88 dias) |
| `revenue`, `employees`, `account_age_years` | 0,47–0,49 | Não usar | Sem sinal |

**Variáveis proibidas como preditoras** (desfecho ou vazamento):

| Variável | Problema | Prova |
|---|---|---|
| `close_value` | Igual a 0 em todo Lost e nulo em todo aberto | AUC = 1,000 |
| `close_date`, `cycle_days`, `close_to_list_ratio` | Só existem depois do fechamento | AUC de `cycle_days` = 0,578, que parece sinal mas é vazamento |
| `account_missing` | Só ocorre em abertos (0 de 6.711 fechados) | Separaria perfeitamente "fechado" de "aberto" |
| `engage_month` | Truncamento à esquerda e censura à direita (seção 9) | Win rate de 81% em 2016 é artefato |

Essas decisões já estão aplicadas no motor de scoring (Valor 60 / Momento 40 / Chance 0). A Etapa 02 confirma, com testes estatísticos, o que o backtest havia indicado.

---

## 9. Data leakage e viés de seleção

### 9.1 Vazamento de informação
- `close_value`, `close_date`, `cycle_days` e `close_to_list_ratio` estão marcados como **desfecho** no dicionário (`COLUMN_ROLES`) e são nulos nos abertos. Há teste garantindo isso.
- **Conta ausente depende do desfecho:** ocorre só em deals abertos. **[H]** O CRM provavelmente só exige a conta no fechamento. Qualquer modelo treinado com fechados nunca veria esse caso.
- O win rate histórico por vendedor/produto foi calculado no backtest apenas com deals fechados **antes** da data de cada snapshot.

### 9.2 Viés de seleção

| Viés | Evidência [FATO] | Efeito |
|---|---|---|
| **Truncamento à esquerda** | O primeiro fechamento é de 01/03/2017, mas há 1.185 deals engajados antes disso | Deals engajados entre nov e dez/2016 têm win rate de 81–82% e ciclo mediano de 90–114 dias: só "sobreviveram" ao recorte os que fecharam tarde, que são mais ganhos |
| **Censura à direita** | O dataset termina em 31/12/2017 | Deals engajados no fim de 2017 só aparecem como fechados se fecharam rápido (ciclo mediano de 10–11 dias em nov–dez) |
| **Pipeline aberto anômalo** | 81% do Engaging tem mais de 138 dias; 34% dos deals engajados em jul/2017 e 32% dos de ago/2017 continuam abertos, contra 8–21% nos demais meses | **[H]** Os abertos não são uma amostra do mesmo processo que gerou os fechados. Isso limita qualquer extrapolação |
| **Sobrevivência de vendedores** | 5 vendedores sem deals; 3 sem deals abertos | Comparações de desempenho só valem para quem tem histórico |

### 9.3 Sinais de dados sintéticos [H]
- O ciclo mediano oscila por trimestre: deals engajados em abr, jul e out/2017 têm mediana de 8–9 dias, contra 61–91 dias nos demais meses de jan a set.
- As datas de engajamento são uniformes nos 7 dias da semana: 1.153 a 1.233 por dia, incluindo sábado e domingo.
- Não há relação entre preço e conversão, nem entre porte e conversão.

Isso não invalida a ferramenta, mas explica a falta de sinal preditivo. Com dados reais, o mesmo pipeline e os mesmos testes mostrariam se o sinal existe.

---

## 10. Limitações

- **Não há registro de atividades** (e-mails, ligações, reuniões, mudanças de estágio com data). O "esfriamento" real de um deal não é observável. Nenhuma data de atividade foi inventada.
- **Não há data de criação nem data prevista de fechamento** para os deals abertos.
- O "hoje" (31/12/2017) é uma premissa: a última data do CRM.
- O holdout temporal tem 1.985 deals no teste. Um AUC de 0,52 tem margem de erro de cerca de ±0,03, então é compatível com acaso.
- As faixas de porte usam quartis das 85 contas. Com 85 empresas, há em média 87 deals por conta (7.375 deals com conta), o que concentra o peso de poucas empresas.
