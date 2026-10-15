# 02 — Technical Architecture: Lead Scorer

> Princípio-guia: **o mais simples que roda na máquina do avaliador na primeira tentativa e que outro dev entende em 15 minutos.**
> Convenção: **[FATO-DADO]** verificado nos CSVs · **[HIPÓTESE]** decisão/premissa a validar · **ADR-n** decisão arquitetural registrada.

---

## 1. Visão geral

```
data/*.csv  ──►  data_loader.py  ──►  scoring.py  ──►  explain.py  ──►  app.py (Streamlit)
 (4 CSVs)       limpeza + joins     score 0–100     motivos + ação      filtros, lista,
                + validação         por componente  em português        detalhe, "como funciona"
                                         ▲
                                   config.py (pesos, data de referência, limiares)
```

- Processo único, sem banco, sem API, sem serviço externo.
- Todo o cálculo roda em memória ao abrir o app (~8.800 linhas → < 1 s), com cache do Streamlit.
- Scoring e explicação são **funções puras** sobre DataFrames — testáveis sem UI.

### Estrutura de pastas proposta

```
submissions/<nome>/
├── README.md                  ← template do desafio (exec summary, process log...)
├── solution/
│   ├── app.py                 ← só UI (Streamlit)
│   ├── lead_scorer/
│   │   ├── __init__.py
│   │   ├── config.py          ← pesos, limiares, data de referência
│   │   ├── data_loader.py     ← leitura, normalização, joins, validação
│   │   ├── scoring.py         ← componentes do score + faixa
│   │   └── explain.py         ← textos de motivo e ação recomendada
│   ├── data/                  ← 4 CSVs originais (CC0)
│   ├── analysis/
│   │   └── backtest.py        ← validação point-in-time (gera números da pág. "Como funciona")
│   ├── tests/
│   │   ├── test_data_loader.py
│   │   └── test_scoring.py
│   ├── requirements.txt       ← streamlit, pandas, pytest (versões fixas)
│   └── README.md              ← Setup / Lógica / Limitações
├── process-log/
└── docs/                      ← estes 3 documentos
```

---

## 2. Decisões arquiteturais (ADRs)

### ADR-1 — Stack: Python + Streamlit

| Opção | Prós | Contras |
|---|---|---|
| **Streamlit** ✅ | Filtros/tabelas/tooltips prontos; mesma linguagem da análise (pandas); deploy gratuito com URL (Streamlit Community Cloud); ~150 linhas de UI | Requer Python no avaliador; UI menos customizável; re-execução do script a cada interação |
| HTML + JS estático | Zero instalação; GitHub Pages | Scoring reescrito em JS (duplica a lógica da análise); mais tempo de UI |
| React + API (FastAPI) | Mais "produto" | 2 processos, build, CORS — risco alto de "não roda" em 6h |
| Planilha | Familiar ao vendedor | Explicação por deal e filtros ficam frágeis; difícil testar |

**Decisão:** Streamlit. O critério nº 1 do desafio é "funciona de verdade"; o maior risco em 6h é tempo de UI e setup. **Trade-off aceito:** visual menos customizado e dependência de Python. Mitigação: `requirements.txt` com versões fixas + URL pública como alternativa.

### ADR-2 — Score por regras ponderadas, não ML

**Contexto [FATO-DADO]:** em holdout temporal, win rate histórico por vendedor/produto/conta/setor/região/manager tem AUC 0,48–0,52. Em snapshots point-in-time (abr, jun, ago, out/2017), a idade do deal sozinha também tem AUC 0,46–0,56. Ou seja: **nenhuma feature disponível prevê Won vs Lost de forma útil.**

**Decisão:** score aditivo de regras com pesos explícitos, onde cada componente mede algo que o vendedor reconhece (valor, momento, chance). Um modelo de ML não melhoraria a predição (não há sinal) e pioraria a explicabilidade.

**Trade-off:** o score é uma **regra de priorização de negócio**, não uma probabilidade calibrada. Isso é dito na UI. A página "Como funciona" publica os AUCs para não vender precisão que não existe.

### ADR-3 — Explicações determinísticas (templates), não LLM

**Decisão:** cada componente gera um motivo por template ("Valor alto: GTX Pro, US$ 4,8k — top 30% do catálogo").
**Prós:** reproduzível, auditável, sem API key, sem custo, sem alucinação, testável.
**Trade-off:** texto menos natural. Aceitável: o vendedor precisa de clareza, não de prosa.

### ADR-4 — Data de referência configurável

**Contexto [FATO-DADO]:** última data do dataset = 31/12/2017; não há "hoje".
**Decisão:** `REFERENCE_DATE = max(engage_date, close_date)` por padrão, sobrescrevível em `config.py`, e exibida no topo do app ("Pipeline em 31/12/2017").
**Trade-off:** usar a data real de hoje deixaria todos os deals com ~9 anos — inútil. Usar o máximo do dataset é a simulação mais fiel de "segunda de manhã".

### ADR-5 — CSVs versionados no repositório

**Decisão:** copiar os 4 CSVs (≈ 640 KB, licença CC0) para `solution/data/`.
**Trade-off:** duplica dados do Kaggle, mas elimina o passo "crie conta no Kaggle e baixe" — que é o ponto de falha mais provável no setup do avaliador.

### ADR-6 — Sem banco de dados, sem autenticação

Dados estáticos e pequenos; o "login" é o seletor de vendedor. Adicionar persistência ou auth não melhora nenhum critério de avaliação e aumenta superfície de falha. Documentado em "para escalar".

---

## 3. Camada de dados (`data_loader.py`)

| Passo | Regra | Justificativa |
|---|---|---|
| Leitura | 4 CSVs, `engage_date`/`close_date` como data | — |
| Normalização de produto | `GTXPro` → `GTX Pro` | [FATO-DADO] 1.480 deals sem preço no join sem isso |
| Normalização de setor | `technolgy` → `technology` | [FATO-DADO] typo na fonte |
| Joins | pipeline ⟕ sales_teams (agent) ⟕ products (product) ⟕ accounts (account) — todos *left join* | Não perder deals sem conta (68% dos abertos) |
| Validação (falha alto) | todo deal tem preço; todo deal tem vendedor/manager/região; `deal_stage` ∈ {4 valores} | Erro silencioso de join é o bug mais provável e mais grave |
| Derivados | `is_open`, `age_days = REFERENCE_DATE − engage_date` (Engaging), `cycle_days` (fechados), `has_account` | Entradas do scoring |

---

## 4. Modelo de scoring (`scoring.py`)

> **Atualização pós-backtest:** os pesos adotados são **Valor 60 / Momento 40 / Chance 0**. A chance continua calculada e exibida como informação. Com 50/30/20, ela só reduzia o valor capturado (45,6% vs 48,3% nos top 20%), sem melhorar a previsão (AUC 0,50). A tabela abaixo registra o desenho original.

Todos os parâmetros abaixo vivem em `config.py`. Valores são **[HIPÓTESE] iniciais**, a calibrar na Etapa 2 com o backtest.

### 4.1 Componentes

| Componente | Pontos | Cálculo | Evidência / racional |
|---|---|---|---|
| **Valor** | 0–50 | `50 × (log(price) − log(min)) / (log(max) − log(min))` | [FATO-DADO] preço varia 490× e o valor fechado ≈ preço de lista (mediana 0,998). Log impede que o GTK 500 domine tudo e cumpre "não é só ordenar por valor". |
| **Timing** | 0–30 | Função da idade vs. curva histórica de ciclo dos deals **ganhos**: máximo entre p25–p75 dos Won (≈ 9–88 dias), decai linearmente até p95 (114 d), 0 após o máximo (138 d) | [FATO-DADO] nenhum deal fechou após 138 dias. [HIPÓTESE] deals dentro da janela típica de fechamento são os mais "acionáveis agora". **Nota de honestidade:** a idade não prevê Won/Lost (AUC ≈ 0,5); o timing mede *urgência/oportunidade de ação*, não chance. |
| **Probabilidade** | 0–20 | Win rate bayesiano: `(wins + k·p₀)/(n + k)` para vendedor×produto, com `p₀` = win rate global (63,2%), `k` = 50; reescalado para 0–20 em torno da média | [FATO-DADO] dispersão vendedor 55–70% mas AUC 0,52 → maior parte é ruído. Shrinkage forte + peso baixo. |

**Score = Valor + Timing + Probabilidade** (0–100, arredondado).

### 4.2 Faixas (o que o vendedor realmente lê)

A faixa é decidida **antes** do score — o score ordena *dentro* da faixa. Isso resolve o risco de 81% do pipeline ser estagnado e virar uma lista inútil.

| Faixa | Regra | Ação recomendada (template) |
|---|---|---|
| 🔴 **Requalificar** | Engaging com `age_days > 138` | "Parado há N dias — mais que qualquer deal já fechado. Confirme se ainda está vivo ou encerre." |
| 🟢 **Prioridade Alta** | Engaging ativo e score ≥ limiar Alta | "Foque esta semana: valor relevante e no momento típico de fechamento." |
| 🟡 **Prioridade Média** | Engaging ativo e score entre limiares | "Mantenha cadência." |
| ⚪ **Prioridade Baixa** | Engaging ativo e score abaixo do limiar | "Baixo valor/momento — trate em lote." |
| 🔵 **Qualificar** | Prospecting (sem `engage_date`) | "Ainda não engajado — qualifique e marque reunião." |
| ➕ Selo **Completar CRM** | `account` vazio (qualquer faixa) | "Conta não informada — preencha para melhorar a análise." |

Limiares Alta/Média definidos por **quantis** do score dos deals ativos (ex.: top 25% = Alta) **[HIPÓTESE]**, para garantir lista curta por vendedor (meta ≤ 10–15 deals Alta).

### 4.3 Contrato de saída

`score_pipeline(df, config) -> DataFrame` com colunas:
`opportunity_id, sales_agent, manager, regional_office, account, product, deal_stage, age_days, price, score, score_value, score_timing, score_prob, band, reasons (list[str]), action (str), needs_crm_fix (bool)`

A UI só lê esse DataFrame — **nenhuma regra de negócio em `app.py`**.

---

## 5. Explicabilidade (`explain.py`)

Para cada deal:
1. **Barra de composição** do score (Valor / Timing / Probabilidade) — mostra *de onde* vêm os pontos.
2. **2–3 motivos** em português, ordenados pela contribuição: o maior e o menor componente.
   Ex.: "✅ Valor alto: GTX Plus Pro (US$ 5,5k)" · "✅ Dia 62 de engajamento — dentro da janela em que deals ganhos costumam fechar (9–88 dias)" · "➖ Chance estimada na média do time (63%)".
3. **Ação recomendada** da faixa.

Regra: nenhum número sem unidade e sem comparação ("62 dias" sozinho não diz nada; "dia 62 de uma janela típica de 9–88" diz).

---

## 6. Interface (`app.py`)

| Área | Conteúdo |
|---|---|
| Sidebar | Seletor de vendedor (default) / manager / região; data de referência exibida |
| Topo | 4 KPIs: deals abertos · valor ativo · valor estagnado · nº "Requalificar" |
| Bloco principal | **"Seu foco esta semana"**: top 5 Alta com motivo e ação |
| Tabela | Todos os deals abertos, agrupáveis por faixa, ordenados por score, com coluna de motivo curto |
| Detalhe | Ao selecionar um deal: composição do score + motivos + ação |
| Aba "Como o score funciona" | Pesos, evidências (gráfico de ciclo histórico), AUCs do backtest, limitações |

---

## 7. Validação (`analysis/backtest.py`)

- **Point-in-time:** para snapshots no fim de cada mês de 2017, reconstruir os deals abertos naquela data (`engage_date ≤ s < close_date`), pontuar só com dados anteriores a `s` e comparar com o resultado real.
- **Métricas:** AUC do componente de probabilidade; % do valor Won capturado pelos top 20% do ranking vs ordem aleatória e vs "só valor".
- **Sem vazamento:** win rates de vendedor×produto calculados apenas com deals fechados antes de `s`.
- Resultados vão para a página "Como funciona" e para o README da submissão.

---

## 8. Qualidade e manutenção

- `pytest` cobrindo: normalização de produto (nenhum deal sem preço), faixas (deal com 139 dias → Requalificar; Prospecting → Qualificar), limites do score (0–100), monotonicidade do Valor, shrinkage (vendedor com n pequeno ≈ média).
- Type hints e docstrings curtas nas funções públicas.
- Sem notebooks no caminho de execução.

---

## 9. Para escalar (vai para "Limitações" do README)

| Necessidade | Mudança |
|---|---|
| Dados ao vivo | Trocar `data_loader` por conector do CRM (Salesforce/HubSpot) com job diário |
| Sinal real de "esfriamento" | Histórico de atividades (e-mails, calls, mudanças de stage) — maior ganho esperado de poder preditivo |
| Probabilidade de verdade | Com atividades + mais stages, treinar modelo e **calibrar**; manter a camada de explicação |
| Multiusuário | Auth (SSO) + filtro automático pelo vendedor logado |
| Feedback loop | Registrar a ação tomada e o resultado para recalibrar pesos trimestralmente |
