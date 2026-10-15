# 08 — Quality Assurance & Technical Audit

> Etapa 05 — auditoria técnica e funcional do Lead Scorer. O objetivo foi encontrar e corrigir falhas, não adicionar funcionalidades.
> A numeração segue o pedido: não existem docs 06 e 07, porque as etapas 03 e 04 não foram solicitadas separadamente.
> Todos os testes citados foram **executados**; nenhum resultado foi presumido.

## 1. Resumo

| Gravidade | Encontrados | Corrigidos | Pendentes |
|---|---|---|---|
| **P0** — impede o funcionamento | 1 | 1 | 0 |
| **P1** — compromete confiança ou decisão | 3 | 3 | 0 |
| **P2** — compromete parte da usabilidade | 5 | 5 | 0 |
| **P3** — melhoria não essencial | 5 | 3 | 2 |

Depois das correções:
- **Testes:** 41 passando (eram 30), nos dois ambientes abaixo.
- **Filtros:** as 37 combinações (27 vendedores, 6 managers, 3 regiões e o time todo) rodam sem exceção, nos dois ambientes.
- **Ambiente mínimo:** Python 3.11 com as versões mínimas do `requirements.txt` (pandas 2.2.2, numpy 2.0.0, streamlit 1.49.0).
- **Ambiente atual:** Python 3.14 com as versões mais recentes (pandas 3.0.6, numpy 2.5.4, streamlit 1.66.0).

## 2. Método

| Área | Como foi testado |
|---|---|
| Dados | Totais recalculados direto do CSV bruto, sem usar o código do app, e comparados com o que o app mostra |
| Scoring | Escala, idades nos limites (0, 8, 9, 88, 89, 116, 117, 137, 138, 139, 1000 dias e nulo), coerência entre segmento e texto, posição real de cada produto, regra das faixas, data de referência alternativa (30/06/2017) e histórico degenerado |
| Aplicação | Streamlit AppTest (todas as opções de cada filtro, nenhuma faixa selecionada, CSV ausente) e navegador real (ordenação, seleção de linha, troca de vendedor) |
| Setup | Venvs limpos com as versões **mínimas** e **mais recentes** aceitas pelo `requirements.txt`; app servido por `streamlit run` e aberto no navegador |
| Manutenção | Leitura do código: duplicação, exceções, organização e dependências |

Os scripts de auditoria ficaram fora do repositório (scratchpad da sessão). As verificações que importam viraram testes permanentes em `solution/tests/test_qa_regressions.py`.

## 3. Problemas encontrados e corrigidos

### QA-01 · **P0** · A troca de filtro derrubava o app (`IndexError`)
- **Sintoma:** com uma linha selecionada na tabela, trocar para um vendedor com menos deals exibia um traceback no lugar da tabela. Reproduzido: Maureen Marcano, linha 17 de 18 → Hayden Neloms (6 linhas).
- **Causa:** o Streamlit guarda a seleção como *posição* da linha, numa chave fixa (`key="active"`). A posição 17 continuava selecionada para uma tabela de 6 linhas, e `data.iloc[17]` falhava.
- **Correção:** a chave da tabela passou a depender dos deals exibidos (`hash` dos IDs). Trocar de vendedor, visão ou faixa zera a seleção. Também há uma checagem de limite antes do `iloc`.
- **Evidência:** antes, [`06-qa-p0-indexerror-troca-vendedor.jpg`](../process-log/screenshots/06-qa-p0-indexerror-troca-vendedor.jpg). Depois, mesmo roteiro no navegador sem erro e com a seleção zerada: [`07-qa-p0-corrigido-troca-vendedor.jpg`](../process-log/screenshots/07-qa-p0-corrigido-troca-vendedor.jpg).

### QA-02 · **P1** · A seleção "pulava" para outro deal ao trocar o filtro
- **Sintoma:** quando a posição antiga ainda existia na nova tabela, a caixa de seleção aparecia marcada num deal que o vendedor não clicou (visível no screenshot 06). O detalhe abriria um deal diferente do escolhido.
- **Causa:** a mesma do QA-01.
- **Correção:** a mesma do QA-01.
- **Evidência:** screenshot 07. Também conferi no navegador, antes e depois, que ordenar a tabela por Score e clicar na primeira linha abre o deal certo (H0RRUQZ6, score 21).

### QA-03 · **P1** · Mudar a data de referência vazava o futuro
- **Sintoma:** o README e o app dizem que a data de referência é ajustável em `config.py`. Com `reference_date = 30/06/2017`:
  - o histórico do score usava **4.032 deals fechados depois dessa data**;
  - a lista trazia **873 deals que ainda não tinham sido engajados**, com idade negativa;
  - deals que estavam abertos na data e fecharam depois ficavam de fora.
- **Causa:** `build_priority_list` separava abertos de fechados pelo estágio *atual* do CRM, não pelo estágio *naquela data*.
- **Correção:** nova função `split_at_reference`:
  - o histórico só inclui deals fechados até a data;
  - os deals abertos são os engajados até a data e ainda sem fechamento nela, mais os nunca engajados;
  - para esses deals, estágio, data e valor de fechamento são reconstruídos como eram naquele dia.
- **Evidência:** com 30/06/2017, 0 deals com engajamento futuro e 0 idades negativas. A lista tem 2.186 deals (1.686 abertos na data + 500 nunca engajados), e o win rate base é igual ao dos deals fechados até a data. Testes: `test_past_reference_uses_only_history_known_at_that_date` e `test_past_reference_lists_deals_as_they_were`. Com a data padrão, nada muda: 2.089 deals, 1.291 em Requalificar e backtest em 48,3% (`test_default_reference_is_unchanged`).

### QA-04 · **P1** · As versões mínimas declaradas não funcionavam
- **Sintoma 1:** `pandas>=2.2` permitia pandas 2.2.0. O pip combinava numpy 1.26 com pyarrow recente, e toda tabela de deals falhava com `ImportError: pyarrow requires NumPy 2.0`.
- **Sintoma 2:** `streamlit>=1.46` permitia 1.46–1.48, que não aceitam `width="stretch"` em `st.dataframe`. Toda tabela falhava com `TypeError`.
- **Causa:** o intervalo de versões foi escrito sem ser testado no limite inferior. No ambiente de desenvolvimento só rodavam as versões mais recentes.
- **Correção:** `pandas>=2.2.2`, `numpy>=2.0` e `streamlit>=1.49`. O 1.49 foi escolhido conferindo o código-fonte das versões 1.47 a 1.50, não por palpite. O README agora pede Python 3.11+, a versão realmente testada.
- **Evidência:**
  - Antes: ambiente mínimo com os dois erros acima, vistos no navegador.
  - Depois: Python 3.11 com pandas 2.2.2, numpy 2.0.0 e streamlit 1.49.0, servido por `streamlit run`: página completa sem erro, 41 testes e 37 combinações de filtro passando.
  - Teste permanente: `test_requirements_pin_numpy_2_and_compatible_pandas`.

### QA-05 · **P2** · As faixas não seguiam a porcentagem documentada
- **Sintoma:** a documentação dizia "top 25% = Alta", mas a Alta tem 30,5% dos deals ativos (Média 29,5%, Baixa 39,9%).
- **Causa:** o corte usa `score >= percentil 75`, e muitos deals empatam no corte (mesmo produto e mesma janela de momento). Todos os empatados sobem para a Alta.
- **Correção:** desempatar arbitrariamente seria injusto entre deals idênticos. Mantive a regra e corrigi a documentação: README, `config.py` e a aba "Como funciona", que agora mostra a porcentagem real calculada.
- **Evidência:** `test_bands_follow_documented_percentile_rule` confere a faixa de cada deal ativo contra a regra escrita.

### QA-06 · **P2** · O texto de valor exagerava
- **Sintoma:** o MG Advanced, 4º de 7 em preço, aparecia como "entre os produtos mais caros do catálogo".
- **Causa:** o rótulo vinha de faixas da escala logarítmica, não da posição real.
- **Correção:** o motivo agora diz a posição exata, por exemplo "o 4º mais caro dos 7 produtos", "o mais caro" ou "o mais barato".
- **Evidência:** `test_value_reason_states_real_price_rank`, para o GTK 500, o MG Advanced e o MG Special.

### QA-07 · **P2** · Possíveis duplicatas apareciam sem aviso
- **Sintoma:** 13 deals abertos têm um "gêmeo" com mesmo vendedor, produto, conta e data de engajamento (12 entre abertos e 1 cujo gêmeo já fechou). O vendedor os via como deals independentes.
- **Causa:** o pipeline de dados (Etapa 02) marcava esses deals, mas o loader do app não usava a marcação.
- **Correção:** a flag `possible_duplicate` entrou no loader do app, e o deal ganha o motivo "⚠️ Possível duplicata… Confirme no CRM antes de trabalhar os dois". Nada é removido automaticamente, porque não há como saber se é erro ou venda legítima.
- **Evidência:** `test_possible_duplicates_are_flagged`. `test_app_loader_agrees_with_pipeline` garante que app e pipeline marcam os mesmos deals.

### QA-08 · **P2** · CSV ausente mostrava um traceback com caminhos locais
- **Sintoma:** sem os dados, o vendedor via um stack trace do Python.
- **Correção:** o carregamento captura `FileNotFoundError`, `DataValidationError` e `ValueError`, mostra uma mensagem em português dizendo o que conferir e para a execução.
- **Evidência:** AppTest numa cópia sem `products.csv`: 0 exceções, com a mensagem "Não foi possível carregar os dados do CRM…".

### QA-09 · **P2** · Informação repetida e desnecessária nos cards
- **Sintoma:** cada card repetia uma frase longa explicando por que a chance não pontua.
- **Correção:** o texto ficou curto ("Informativo: não entra no score (veja *Como o score funciona*)"), e o porquê aparece uma vez, na aba de metodologia.

### QA-10 · **P3** · Pequenos ajustes de interface (corrigidos)
- A coluna "Vendedor" era redundante na visão de um único vendedor e foi removida nessa visão.
- O título "Seu foco esta semana" aparecia na visão de manager e região. Lá, agora é "Foco da semana".
- A legenda dizia "última data do CRM" mesmo com a data alterada. Agora diz "data de referência; ajustável em `config.py`".

### QA-11 · **P3** · Histórico degenerado (corrigido)
- **Sintoma:** um histórico sem nenhum deal ganho gerava quantis `NaN` em silêncio, e quantis coincidentes causariam divisão por zero no Momento.
- **Correção:** erro claro ("é preciso ao menos um deal ganho…") e divisores com piso de 1 dia.
- **Evidência:** `test_history_without_wins_raises_clear_error` e `test_timing_handles_coincident_quantiles`.

### QA-12 · **P3** · AppTest não importava o pacote em versões antigas (corrigido)
- **Correção:** `app.py` adiciona a própria pasta ao `sys.path`. O app passa a funcionar seja qual for o diretório de execução, e o AppTest roda no Streamlit 1.49.

## 4. Verificações sem defeito

| Item auditado | Resultado |
|---|---|
| Integridade dos relacionamentos | 0 deals sem preço, 0 sem manager e 0 contas informadas sem setor |
| Duplicação indevida por join | 8.800 linhas e 8.800 IDs únicos; 2.089 abertos no app = 2.089 no CSV bruto |
| Totais | Valor aberto US$ 4.966.215 e valor parado US$ 3.198.664 (1.291 deals), iguais no app e no cálculo direto do CSV. KPIs de Maureen (US$ 40.823 / 99.402) e Anna (US$ 77.900 / 95.359) conferidos |
| Ausentes | Prospecting sem idade (0 com idade), 0 scores nulos e 0 deals sem motivo |
| Escala | Mínimo 0, máximo 95; o teto teórico é 100 (60 + 40). Score = soma dos componentes em todos os deals |
| Momento nos limites | 0 dias = 20 pts; de 9 a 88 = 40 (máximo); 116 = 20; 138 = 0; 139 em diante = 0, já em Requalificar; nulo = 0 |
| Coerência das explicações | 0 deals com texto de momento diferente do seu segmento |
| Ordem da lista | Faixa crescente e score decrescente dentro de cada faixa: confirmado |
| Vazamento na data padrão | O score usa só `sales_price` e a idade; a chance tem peso 0; o backtest usa só o que se sabia em cada snapshot |
| Estados vazios | Nenhuma faixa selecionada: 0 exceções. Não existe vendedor só com deals parados (mínimo de 6 deals não parados por vendedor), então a mensagem de "nenhum deal ativo" não aparece com estes dados |
| Seleção após ordenar | Ordenar por Score e clicar abre o deal correto |

## 5. Limitações pendentes

| ID | Gravidade | Pendência | Por que ficou |
|---|---|---|---|
| QA-13 | P3 | A limpeza dos dados (correções de grafia, flag de duplicata) existe em dois lugares: `lead_scorer/data_loader.py`, do app, e `src/data_processing.py`, do pipeline auditável | Unificar exigiria refatorar o app na etapa de auditoria. O risco está coberto por `test_app_loader_agrees_with_pipeline`, que falha se os dois divergirem |
| QA-14 | P3 | Python 3.10 não testado | Não estava disponível nesta máquina. O README passou a pedir 3.11+, a menor versão testada |
| — | — | **CA9** (pessoa não técnica acha o top 5 e entende o motivo em menos de 30 s) **não foi verificado** | Exige um teste com uma pessoa real. Não declaro como aprovado |
| — | — | Data de referência anterior: deals em Prospecting sem nenhuma data entram em qualquer data de referência | O dataset não tem data de criação, então é impossível saber quando o prospect surgiu. Documentado na docstring de `split_at_reference` |

## 6. Status dos critérios de aceite (doc 03)

| # | Critério | Status | Evidência |
|---|---|---|---|
| CA1 | Roda em ambiente limpo com `pip install` + `streamlit run` | ✅ Atendido | Venvs limpos: Python 3.11 nas versões mínimas e Python 3.14 nas mais recentes |
| CA2 | 4 CSVs reais; 8.800 deals; 2.089 abertos | ✅ Atendido | `test_all_tables_loaded_with_expected_columns`, `test_record_counts_reconcile` |
| CA3 | Nenhum deal sem preço | ✅ Atendido | `test_every_deal_has_a_price`, `test_relationships_resolve` |
| CA4 | Filtros por vendedor, manager e região | ✅ Atendido | 37/37 combinações via AppTest e teste manual no navegador |
| CA5 | Score 0–100, faixa, ≥ 2 motivos e 1 ação por deal | ✅ Atendido | `test_every_open_deal_is_scored_and_explained` |
| CA6 | Score ≠ ordenar por valor | ✅ Atendido | `test_score_is_not_just_sorting_by_value` (Spearman 0,75) |
| CA7 | Mais de 138 dias → Requalificar | ✅ Atendido | `test_stale_deals_go_to_requalify` |
| CA8 | No máximo 15 deals em Alta por vendedor | ✅ Atendido | Máximo de 8 (`test_short_high_priority_list_per_agent`) |
| CA9 | Pessoa não técnica entende o top 5 em menos de 30 s | ⏳ **Pendente** | Precisa de teste com uma pessoa |
| CA10 | README com Setup, Lógica e Limitações | ✅ Atendido | `solution/README.md`, atualizado nesta etapa |
| CA11 | Backtest com AUC publicado | ✅ Atendido | Aba "Como funciona" e README (48,3% de captura; AUC 0,50) |
| CA12 | Process log com iterações e erros | ✅ Atendido | `process-log/`, agora com os screenshots 06–07 |
| CA13 | `pytest` verde | ✅ Atendido | 41/41 nos dois ambientes |

**Critérios de auditoria desta etapa:** todos os P0 e P1 foram corrigidos e verificados com teste executado. Ficam pendentes 2 itens P3 e o CA9, que depende de uma pessoa.
