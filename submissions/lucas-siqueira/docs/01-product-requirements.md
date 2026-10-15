# 01 — Product Requirements: Lead Scorer (Challenge 003)

> **Registro histórico (Etapa 01):** este documento é o plano original, aprovado antes da implementação. O estado atual está no [README da submissão](../README.md) e nos docs 08–10 (por exemplo, os pesos passaram de 50/30/20 para 60/40/0, e a tabela foi refeita).

> Etapa 01 — Discovery. Nenhum código de produto foi escrito.
> Convenção usada neste documento:
> - **[FATO-REPO]** — está escrito no repositório do desafio (README, submission guide, CONTRIBUTING).
> - **[FATO-DADO]** — verificado por mim nos CSVs (scripts de EDA no process log; números reproduzíveis).
> - **[HIPÓTESE]** — inferência ou decisão minha, ainda não validada.

---

## 1. Problema central de negócio

**[FATO-REPO]** A Head de RevOps diz: vendedores "gastam tempo demais em deals que não vão fechar e deixam oportunidades boas esfriar". Pede "uma ferramenta que o vendedor abra, veja o pipeline, e saiba onde focar". Rejeita explicitamente "um modelo no Jupyter Notebook que ninguém vai usar".

**Reformulação:** o problema não é *prever* o resultado de um deal; é **alocar a atenção limitada do vendedor** no pipeline aberto. São duas dores distintas, e a ferramenta precisa atacar as duas:

| Dor | O que significa | Como a ferramenta responde |
|---|---|---|
| Tempo em deals que não fecham | Deals parados muito além do ciclo normal continuam "abertos" e consumindo atenção | Sinalizar deals **estagnados** e recomendar requalificar ou encerrar |
| Deals bons esfriando | Deals de alto valor, ainda dentro da janela normal de fechamento, sem foco | Colocar no topo deals com **maior valor esperado dentro da janela ativa** |

### O que os dados mostram (e que muda o produto)

| # | Achado | Tipo |
|---|---|---|
| D1 | Pipeline: 8.800 deals — 4.238 Won, 2.473 Lost, 1.589 Engaging, 500 Prospecting. **Pipeline acionável = 2.089 deals abertos.** | FATO-DADO |
| D2 | Win rate histórico global = **63,2%** (Won / fechados). | FATO-DADO |
| D3 | Win rate quase plano entre categorias: produto 60–65%, região 63–64%, manager 62–64%, setor 61–65%, quartis de receita/funcionários 61–66%. | FATO-DADO |
| D4 | Em holdout temporal (treino até set/2017, teste out–dez/2017), win rate histórico por vendedor, produto, conta, setor, região ou manager tem **AUC entre 0,48 e 0,52** — equivalente a cara-ou-coroa. | FATO-DADO |
| D5 | Ciclo engage→close dos deals fechados: máximo **138 dias**, p95 = 114 dias, mediana Won = 57 dias, mediana Lost = 14 dias. **50% dos Lost morrem em até 14 dias.** | FATO-DADO |
| D6 | Usando 31/12/2017 como "hoje", **81% dos deals em Engaging (1.291) já estão abertos há mais de 138 dias** — mais velhos do que qualquer deal que já fechou na história do dataset. Idade mediana: 165 dias. | FATO-DADO |
| D7 | **68% dos deals abertos não têm `account` preenchido** (1.088 Engaging + 337 Prospecting). Features de conta são inutilizáveis para a maioria do pipeline aberto. | FATO-DADO |
| D8 | Prospecting não tem `engage_date` → não há como medir idade desses 500 deals. | FATO-DADO |
| D9 | Preço de lista varia **~490×** (MG Special US$ 55 → GTK 500 US$ 26.768). O valor fechado fica em ~100% do preço de lista (mediana 0,998). Logo, `sales_price` é um bom estimador de valor do deal aberto. | FATO-DADO |
| D10 | Qualidade: produto `GTXPro` no pipeline ≠ `GTX Pro` no catálogo (1.480 linhas); setor `technolgy` com erro de digitação; 5 vendedores em `sales_teams` sem nenhum deal; 3 vendedores sem deal aberto. | FATO-DADO |
| D11 | Deals engajados em 2016-Q4 têm win rate de 82% vs ~60% depois — provável **viés de sobrevivência** no recorte do dataset (só entram deals fechados a partir de mar/2017). | FATO-DADO (número) / HIPÓTESE (causa) |
| H1 | O dataset é sintético (origem Maven Analytics/Kaggle), o que explica D3/D4. | HIPÓTESE |

**Implicação de produto (decisão central):** um score que finge prever vitória a partir de vendedor/produto/setor estaria **vendendo ruído com cara de precisão**. Isso é exatamente o que um baseline de IA genérico faria. Nossa diferenciação é ser honesto sobre o que o dado sustenta:

1. **Valor** é o diferenciador real entre deals (D9).
2. **Tempo/estagnação** é o sinal operacional mais forte e mais acionável (D5, D6).
3. **Probabilidade de ganho** entra como componente com *shrinkage* forte para a média — e a UI comunica que é uma estimativa de baixa confiança.
4. **Qualidade de dado** vira ação para o vendedor (completar conta), não um buraco silencioso (D7).

---

## 2. Usuários e momento de uso

| Persona | Pergunta que precisa responder | Frequência |
|---|---|---|
| **Vendedor** (primário, não-técnico) | "Segunda de manhã: em quais 10 deals eu foco esta semana, e o que eu faço em cada um?" | Semanal / diária |
| **Manager** (secundário) | "Quais vendedores do meu time têm pipeline podre ou concentrado? Onde intervir?" | Semanal |
| **Head de RevOps** (sponsor) | "A ferramenta é confiável e explicável?" | Avaliação |

**[HIPÓTESE]** O vendedor tem em média ~77 deals abertos (mediana 79, máx 194 — FATO-DADO). Ninguém prioriza 77 itens; a ferramenta precisa reduzir para uma lista curta acionável.

---

## 3. Requisitos

### 3.1 Obrigatórios — derivados do README [FATO-REPO]

| ID | Requisito | Origem |
|---|---|---|
| R1 | A solução **roda** (não é mockup) | "Precisa rodar" |
| R2 | Usa os **dados reais** do dataset (4 CSVs) | "Precisa usar os dados reais" |
| R3 | Tem **lógica de scoring/priorização que não é só ordenar por valor** | "não é só ordenar por valor" |
| R4 | O vendedor entende **por que** cada deal tem score alto ou baixo | "O vendedor precisa entender por que" |
| R5 | Documentação: **Setup**, **Lógica** (critérios e porquê), **Limitações** (e o que precisa para escalar) | "Documentação mínima" |
| R6 | **Process log** com evidências do uso de IA (sem ele = desclassificado) | README + submission guide |
| R7 | Submissão via PR em `submissions/<nome>/` seguindo o template, sem tocar arquivos fora da pasta | CONTRIBUTING |

### 3.2 Obrigatórios — derivados dos critérios de qualidade [FATO-REPO → requisito meu]

| ID | Requisito de produto | Critério que atende |
|---|---|---|
| R8 | Setup em ≤ 3 comandos, testado em máquina limpa; idealmente URL pública | "Funciona de verdade? Dá pra rodar?" |
| R9 | Score com features justificadas por dados, com evidência de validação | "O scoring faz sentido? Vai além do óbvio?" |
| R10 | Interface em português, sem jargão estatístico, com explicação em linguagem natural por deal | "Vendedor não-técnico consegue usar?" |
| R11 | Cada deal mostra uma **ação recomendada**, não só números | "Ajuda a tomar decisão ou só mostra dados?" |
| R12 | Scoring isolado da UI, com testes e pesos em configuração | "Código limpo pra outro dev manter" |

### 3.3 Funcionalidades do MVP (escopo fechado)

| ID | Funcionalidade | Por que entra |
|---|---|---|
| F1 | **Filtro por vendedor** (default) + filtros por manager e região | Bônus explícito no README; é o modo de uso real |
| F2 | **Lista priorizada** dos deals abertos com score 0–100 e faixa (Prioridade Alta / Média / Baixa / Requalificar) | Núcleo do produto |
| F3 | **Explicação por deal**: decomposição do score em fatores + 1–2 frases ("Valor alto (GTX Plus Pro, US$ 5,5k) e dentro da janela típica de fechamento (dia 62 de ~57–88)") | R4, "explainability ganha" |
| F4 | **Ação recomendada por deal** (ex.: "Avançar para fechamento", "Requalificar ou encerrar — parado há 210 dias", "Completar conta no CRM") | R11 |
| F5 | **Resumo no topo**: nº de deals abertos, valor em pipeline ativo vs estagnado, top 5 da semana | Uso "segunda de manhã" |
| F6 | **Página "Como o score funciona"**: pesos, evidência dos dados e limitações em linguagem simples | Confiança + R5 |

### 3.4 Opcionais — fora do MVP (com motivo)

| Funcionalidade | Decisão | Motivo |
|---|---|---|
| Modelo de ML (XGBoost/logística) | **Não** | D4: features categóricas não predizem; o próprio README diz que regras bem apresentadas valem mais. Fica como análise de validação no process log. |
| Visão de manager agregada (ranking de vendedores) | Opcional, só se sobrar tempo | Útil, mas o filtro por manager já cobre 80% |
| Export CSV da lista | Opcional (≈15 min) | Barato e útil; não é crítico |
| Bot Slack/e-mail, autenticação, escrita no CRM, edição de deals | **Não** | Não contribuem para os critérios; aumentam risco de "não roda" |
| Explicação gerada por LLM | **Não** | Explicações determinísticas por template são mais confiáveis, auditáveis e não exigem API key do avaliador |
| Pesos ajustáveis pelo usuário na UI | **Não** | Confunde o vendedor; pesos ficam em config para o RevOps |

---

## 4. MVP (≤ 6 horas)

**Uma frase:** um app web local (e publicado) onde o vendedor escolhe seu nome e vê seus deals abertos ordenados por um Priority Score explicável, com a ação recomendada para cada um e um alerta claro de deals estagnados.

**Lógica de scoring proposta [HIPÓTESE a validar na Etapa 2]** — detalhada em `02-technical-architecture.md`:

```
Priority Score (0–100) = Valor (até 50) + Timing (até 30) + Probabilidade (até 20)
                         − penalidade de estagnação
```

- **Valor (50%)**: log do preço de lista do produto, normalizado. Log porque o preço varia 490× — sem log o score vira "ordenar por valor" (viola R3).
- **Timing (30%)**: posição do deal em relação à curva histórica de fechamento (D5). Máximo na janela em que deals ganhos costumam fechar; decai além de p95 (114d); zera além do máximo histórico (138d).
- **Probabilidade (20%)**: win rate esperado com shrinkage bayesiano (vendedor × produto encolhido para a média global). Peso baixo **por causa** de D4 — a UI deixa isso explícito.
- **Estagnação**: deals > 138 dias vão para a faixa "Requalificar" independentemente do valor — porque este é o problema que a Head descreveu.
- **Prospecting** (sem data): pontuado só por Valor + Probabilidade, faixa própria "Qualificar".

---

## 5. Indicadores de sucesso

### 5.1 Validáveis dentro do desafio (offline)

| Indicador | Como medir | Meta MVP |
|---|---|---|
| **Funciona** | Clonar em diretório limpo, seguir README, app abre | 100% — testado antes do PR |
| **Tempo até primeira decisão** | Do clique no nome até ver top 5 + ação | < 30 s, sem ler documentação |
| **Cobertura de explicação** | % de deals abertos com explicação + ação | 100% |
| **Honestidade do score** | Backtest point-in-time (snapshots mensais de 2017): o componente de probabilidade não pode ser *pior* que a média (AUC ≥ 0,5) e o relatório publica o AUC real | Publicado na página "Como funciona" |
| **Captura de valor** | Em snapshots históricos: % do valor Won capturado pelos top 20% do ranking vs ordenação aleatória | > aleatório; reportar número |
| **Redução de foco** | Nº médio de deals "Prioridade Alta" por vendedor | ≤ 10–15 (lista curta acionável) |

### 5.2 Para produção (proposta para a Head de RevOps — fora do escopo do desafio)

| Indicador | Por quê |
|---|---|
| Win rate dos deals "Alta" vs "Baixa" (após 1 trimestre) | Valida se a priorização separa resultado |
| Ciclo médio e % de deals > 138 dias (antes vs depois) | Mede se o pipeline podre foi limpo |
| Adoção semanal (vendedores ativos / 30) | Ferramenta que ninguém abre não resolve nada |
| % de deals abertos com `account` preenchido | Mede melhoria da higiene de CRM |

---

## 6. Riscos, limitações dos dados e dependências

| Risco / limitação | Impacto | Mitigação |
|---|---|---|
| Atributos não predizem resultado (D3, D4) | Score de probabilidade é fraco | Peso baixo, shrinkage, transparência na UI; o valor real vem de valor + timing |
| Não existe data "de hoje" no dataset | Idade dos deals depende de uma premissa | Data de referência = última data do dataset (31/12/2017), **configurável** e visível na UI |
| 81% do Engaging já está estagnado (D6) | Se o timing dominar, quase tudo vira "Requalificar" | Tratar estagnação como **faixa/ação**, não só pontos; dentro de cada faixa ordenar por valor+prob. Mostrar o número como insight para a Head |
| 68% sem conta (D7) | Sem dados de setor/porte para a maioria | Score não depende de conta; ausência vira ação "Completar CRM" |
| Prospecting sem data (D8) | Não dá para medir timing | Faixa separada "Qualificar" |
| Inconsistências (D10) | Join quebrado silenciosamente (1.480 deals sem preço) | Normalização explícita + teste automatizado que falha se algum produto ficar sem preço |
| Viés de sobrevivência no início da série (D11) | Infla win rates de deals antigos | Calcular curva de timing com todos os fechados, documentar; não usar trimestre como feature |
| Sem histórico de atividades (e-mails, calls, mudanças de stage) | Não dá para medir "esfriamento" real nem engajamento | Declarado em Limitações; é o primeiro item do "para escalar" |
| Overengineering | Estourar 6h, app não rodar | Escopo fechado na seção 3.3; cortes pré-definidos no plano |
| Dependência: dataset Kaggle | Avaliador precisa baixar dados | CSVs (CC0, ~640 KB) versionados junto com a solução |
| Dependência: hospedagem (Streamlit Community Cloud) | URL pública pode falhar | Setup local é o caminho principal; URL é bônus |
