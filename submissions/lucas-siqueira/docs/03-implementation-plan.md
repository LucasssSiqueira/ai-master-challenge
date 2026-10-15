# 03 — Implementation Plan: Lead Scorer

> Orçamento: **6 horas** (o desafio sugere 4–6h). Já gastos na Etapa 01 (discovery + EDA): ~1h.
> Regra de ouro: **ao final de cada fase existe algo que roda.** Se o tempo apertar, corta-se do fim da lista, nunca a base.

---

## 1. Fases e timebox

| Fase | Entrega | Tempo | Acumulado | Gate de saída |
|---|---|---|---|---|
| **0. Discovery** ✅ | 3 docs + EDA reproduzível | 1h00 | 1h00 | Aprovação do usuário |
| **1. Base de dados** | `data_loader.py` + `config.py` + testes de join | 0h40 | 1h40 | `pytest` verde; 0 deals sem preço; 2.089 abertos |
| **2. Scoring** | `scoring.py` (3 componentes + faixas) + testes | 1h00 | 2h40 | Score 0–100; distribuição de faixas por vendedor sensata (Alta ≤ 15) |
| **3. Explicação** | `explain.py` (motivos + ação) | 0h30 | 3h10 | 100% dos abertos com motivo e ação |
| **4. UI** | `app.py`: filtros, KPIs, "foco da semana", tabela, detalhe | 1h15 | 4h25 | App roda local; fluxo "escolher vendedor → ver top 5" < 30 s |
| **5. Validação** | `backtest.py` + aba "Como funciona" | 0h35 | 5h00 | AUCs e captura de valor publicados |
| **6. Entrega** | README (Setup/Lógica/Limitações), template de submissão, process log, teste em clone limpo, deploy, PR | 1h00 | 6h00 | Checklist da seção 4 completo |

### Plano de corte (se atrasar)

Cortar nesta ordem, sem perguntar: (1) deploy público → fica só local; (2) aba "Como funciona" vira seção do README; (3) backtest reduzido a 1 snapshot; (4) visão de detalhe vira coluna de texto na tabela.
**Nunca cortar:** filtro por vendedor, faixas, motivo + ação por deal, README de setup, process log.

---

## 2. Tarefas detalhadas

### Fase 1 — Base de dados
1. Criar estrutura de pastas (ver arquitetura §1) e `requirements.txt` com versões fixas.
2. Copiar os 4 CSVs para `solution/data/`.
3. `config.py`: `REFERENCE_DATE`, pesos (50/30/20), limiares de ciclo (calculados dos dados, não hard-coded), `K_SHRINKAGE=50`.
4. `data_loader.load()`: leitura, normalização (`GTXPro`, `technolgy`), left joins, derivados, asserts de validação.
5. Testes: nenhum preço nulo; 8.800 linhas preservadas; 2.089 abertos; 1.425 sem conta.

### Fase 2 — Scoring
1. `value_score()` com escala log.
2. `cycle_stats()` a partir dos Won (p25, p75, p95, max) → `timing_score()`.
3. `prob_score()` bayesiano vendedor×produto (só com fechados).
4. `assign_band()` (Requalificar / Alta / Média / Baixa / Qualificar) + flag `needs_crm_fix`.
5. Testes de borda: 138 vs 139 dias; Prospecting; vendedor com n=0; monotonicidade de valor.
6. **Checagem de sanidade manual:** olhar top 10 de 3 vendedores diferentes e perguntar "isso faz sentido para um vendedor?". Registrar no process log o que foi ajustado.

### Fase 3 — Explicação
1. Templates de motivo por componente (alto/médio/baixo) com unidades e comparação.
2. Template de ação por faixa.
3. Teste: nenhum deal aberto sem `reasons` e `action`.

### Fase 4 — UI
1. Sidebar: seletor de vendedor (default), manager, região; data de referência visível.
2. KPIs do topo.
3. "Seu foco esta semana" (top 5 Alta) em cards.
4. Tabela completa com faixa, score, motivo curto; ordenação por faixa → score.
5. Detalhe do deal: barra de composição + motivos + ação.
6. Copy 100% em português, sem jargão ("chance estimada", não "probabilidade posterior").

### Fase 5 — Validação
1. `backtest.py` com snapshots mensais 2017, sem vazamento.
2. Tabela de AUC do componente de probabilidade e captura de valor (top 20%) vs aleatório e vs "só valor".
3. Aba "Como funciona": pesos, gráfico do ciclo histórico, resultados do backtest, limitações.

### Fase 6 — Entrega
1. `solution/README.md`: Setup (3 comandos), Lógica, Limitações + "para escalar".
2. `submissions/<nome>/README.md` a partir do template (exec summary, abordagem, findings, recomendações, process log).
3. Process log: export desta conversa + narrativa dos pontos onde a IA errou/foi corrigida + git history.
4. Teste em clone limpo (`venv` novo) seguindo só o README.
5. Deploy no Streamlit Community Cloud (opcional).
6. PR: `[Submission] <Nome> — Challenge 003`, só arquivos dentro de `submissions/<nome>/`.

---

## 3. Critérios de aceite do MVP

| # | Critério | Como verificar |
|---|---|---|
| CA1 | App abre com `pip install -r requirements.txt` + `streamlit run app.py` em ambiente limpo | Clone novo + venv novo |
| CA2 | Usa os 4 CSVs reais; 8.800 deals carregados; 2.089 abertos exibidos no total | Teste automatizado + KPI na UI |
| CA3 | Nenhum deal perde preço no join (`GTXPro` tratado) | Teste automatizado |
| CA4 | Filtro por vendedor, manager e região funcionando | Teste manual |
| CA5 | Todo deal aberto tem score 0–100, faixa, ≥ 2 motivos e 1 ação | Teste automatizado |
| CA6 | Score **não** equivale a ordenar por valor (correlação de Spearman score×preço < 0,95 e existem deals de menor valor acima de maiores) | Teste automatizado |
| CA7 | Deals com idade > 138 dias estão em "Requalificar" | Teste automatizado |
| CA8 | Vendedor típico vê ≤ 15 deals em "Prioridade Alta" | Inspeção da distribuição |
| CA9 | Um usuário não-técnico identifica o top 5 e entende o motivo do 1º sem ajuda, em < 30 s | Teste de corredor (1 pessoa) |
| CA10 | README contém Setup, Lógica e Limitações | Revisão |
| CA11 | Página/seção com resultado do backtest publicando os AUCs reais | Revisão |
| CA12 | Process log presente e com iterações, erros da IA e correções | Revisão |
| CA13 | `pytest` verde | CI local |

---

## 4. Checklist de execução

**Antes de codar**
- [x] README do desafio, submission guide, CONTRIBUTING e template lidos
- [x] Dataset baixado e explorado; fatos vs hipóteses separados
- [x] Docs 01, 02, 03 escritos
- [ ] **Aprovação do usuário para a Etapa 2**
- [ ] Fork do repositório + branch `submission/<nome>`

**Construção**
- [ ] Fase 1 — dados + testes de join
- [ ] Fase 2 — scoring + testes + sanidade manual em 3 vendedores
- [ ] Fase 3 — explicações + ações
- [ ] Fase 4 — UI
- [ ] Fase 5 — backtest + "Como funciona"

**Entrega**
- [ ] README da solução (Setup / Lógica / Limitações)
- [ ] README da submissão (template)
- [ ] Process log (chat export + narrativa + git history)
- [ ] Teste em clone limpo
- [ ] Deploy (opcional)
- [ ] PR com título no formato correto, só arquivos em `submissions/<nome>/`

---

## 5. Decisões pendentes de aprovação

| Decisão | Proposta | Alternativa |
|---|---|---|
| Stack | Streamlit | HTML+JS estático |
| Pesos | Valor 50 / Timing 30 / Prob. 20 | Ajustar após sanidade manual |
| "Hoje" | 31/12/2017 (fim do dataset) | Outra data configurada |
| Estagnação | Faixa própria "Requalificar" (> 138 dias) | Só penalidade no score |
| Deploy público | Sim, se sobrar tempo | Somente local |
