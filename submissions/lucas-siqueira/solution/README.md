# Lead Scorer

App web em que o vendedor escolhe o próprio nome e vê os deals abertos em ordem de prioridade. Cada deal traz o motivo da posição e a próxima ação recomendada. Deals parados além de qualquer ciclo já visto ficam separados para limpeza.

## Setup

Requer Python 3.11 ou superior. Testado em 3.11 (com as versões mínimas de `requirements.txt`) e em 3.14 (com as mais recentes).

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app abre em http://localhost:8501. Os CSVs do dataset (licença CC0) já estão em `data/`, então não é preciso baixar nada do Kaggle.

Testes e validação histórica:

```bash
python -m pytest
python -m lead_scorer.backtest
```

Pipeline de dados e análise exploratória (detalhes em `docs/04-data-analysis.md` e `docs/05-data-dictionary.md`):

```bash
python -m src.data_processing
python -m src.exploratory_analysis
```

O primeiro comando gera, em `data/processed/`, a tabela analítica, o log de qualidade e a reconciliação de contagens. Os CSVs originais não são alterados.

## Como usar

1. Na barra lateral, escolha **Vendedor** e o seu nome. Managers podem escolher **Manager** ou **Região** para ver também o resumo por vendedor.
2. **Seu foco esta semana** mostra os 5 deals mais importantes, com a ação recomendada e os motivos.
3. A aba **Deals ativos** lista todos os deals. Clique em uma linha para ver a composição do score.
4. A aba **Requalificar** lista os deals parados há mais de 138 dias, do maior valor para o menor.
5. A aba **Como o score funciona** explica a regra e mostra a validação com dados passados.

## Lógica

**Score (0–100) = Valor (até 60) + Momento (até 40).** A chance histórica é calculada e exibida, mas tem peso 0.

| Componente | Cálculo | Por quê |
|---|---|---|
| Valor | Preço de lista do produto em escala logarítmica | O valor fechado fica praticamente igual ao preço de lista (mediana 99,8%), e o preço varia ~490×. Sem o log, o score seria só "ordenar por valor". |
| Momento | Pontuação máxima entre 9 e 88 dias de engajamento (p25–p75 dos deals ganhos). Cai até p95 (116 dias) e zera aos 138 | Mostra se é hora de agir no deal. Nenhum deal do histórico fechou depois de 138 dias. |
| Chance (peso 0, informativa) | Taxa de vitória do vendedor com o produto, com *shrinkage* bayesiano (k = 50) para a média do time (63%) | Aparece nos motivos com o aviso de que não pontua. No histórico, ela não prevê o resultado; com peso 20, só reduzia o valor capturado (ver Validação). |

A **faixa** é decidida antes do score, e o score só ordena os deals dentro de cada faixa:

| Faixa | Regra | Ação |
|---|---|---|
| 🟢 Alta / 🟡 Média / ⚪ Baixa | Engaging com até 138 dias: score ≥ percentil 75, entre os percentis 40 e 75, e o restante. Empates no corte sobem de faixa (hoje: 31% / 30% / 40%) | Fechar, manter cadência ou tratar em lote |
| 🔵 Qualificar | Prospecting, ainda sem data de engajamento | Qualificar e marcar a primeira reunião |
| 🔴 Requalificar | Engaging há mais de 138 dias | Confirmar se o deal está vivo ou encerrar |

Os pesos, limiares e a data de referência ficam em [`lead_scorer/config.py`](lead_scorer/config.py).

### Correções nos dados

- O produto aparece como `GTXPro` no pipeline e `GTX Pro` no catálogo. Sem a correção, 1.480 deals ficariam sem preço.
- O setor `technolgy` foi corrigido para `technology`.
- O carregamento falha com erro explícito se algum deal ficar sem preço ou sem vendedor.

## Validação

Para cada fim de mês de 2017, `lead_scorer/backtest.py` reconstrói os deals abertos naquela data, calcula o score só com o histórico disponível até então e compara com o resultado real.

| Métrica (média de 9 meses) | Resultado |
|---|---|
| Valor ganho nos top 20% do score | 48% |
| …ordenando só por valor | 49% |
| …em ordem aleatória | 20% |
| AUC da Chance / do score total (0,50 = acaso) | 0,50 / 0,50 |

Em resumo: o score concentra mais que o dobro do valor ganho que uma ordem aleatória. Ele fica cerca de 1 ponto abaixo de ordenar só por valor, em troca de separar os deals parados e indicar o momento e a ação de cada um. **Nenhum atributo disponível (vendedor, produto, conta, setor, região ou tempo no pipeline) prevê se o deal será ganho.** Por isso o score é apresentado como uma regra de priorização, não como uma probabilidade.

### Como os pesos foram escolhidos

A primeira versão usava 50/30/20 (Valor/Momento/Chance). O backtest comparou 9 combinações:

| Pesos | Valor ganho nos top 20% | Correlação com "só valor" |
|---|---|---|
| 50/30/20 | 45,6% | 0,78 |
| 60/30/10 | 47,7% | 0,83 |
| **60/40/0 (adotado)** | **48,3%** | **0,75** |
| 70/30/0 | 48,9% | 0,86 |
| 100/0/0 (só valor) | 49,4% | 1,00 |

60/40/0 superou 50/30/20 em 8 de 9 meses (+2,7 pontos em média). Foi a combinação que ficou mais longe de "ordenar por valor" sem perder captura relevante. Pesos maiores no Valor ganham menos de 1 ponto e se aproximam de ordenar só por preço.

## Limitações

- **Sem histórico de atividades.** Não há e-mails, ligações ou mudanças de estágio, que seriam o sinal real de um deal "esfriando". O dado mais valioso a acrescentar é esse.
- **68% dos deals abertos não têm conta.** Setor e porte não entram no score, e o app sinaliza "Conta não informada" para o vendedor completar o CRM.
- **O "hoje" é 31/12/2017**, a última data do dataset. A data é configurável.
- **A validação só usa deals que fecharam.** Os deals abertos hoje não têm resultado conhecido.
- **81% dos deals em Engaging estão parados.** 6 dos 27 vendedores com pipeline não têm nenhum deal ativo e veem apenas deals para qualificar e requalificar.

### Para escalar

| Necessidade | Mudança |
|---|---|
| Dados atualizados | Trocar `data_loader.py` por um conector do CRM (Salesforce/HubSpot) com carga diária |
| Prever o resultado de fato | Incluir atividades e histórico de estágios, treinar um modelo calibrado e manter a camada de explicação |
| Vários usuários | Login (SSO) com filtro automático pelo vendedor logado |
| Aprender com o uso | Registrar a ação tomada e o resultado para recalibrar os pesos a cada trimestre |

## Estrutura

```
app.py                    interface (Streamlit), sem regras de negócio
lead_scorer/config.py     pesos, limiares, data de referência
lead_scorer/data_loader.py leitura, correções, joins, validação
lead_scorer/scoring.py    componentes do score e faixas
lead_scorer/explain.py    motivos e ações em português
lead_scorer/backtest.py   validação com dados passados
src/data_processing.py    pipeline: validação de chaves, limpeza, tabela analítica, log de qualidade
src/exploratory_analysis.py números da análise de dados
tests/                    pytest
data/                     CSVs originais
```
