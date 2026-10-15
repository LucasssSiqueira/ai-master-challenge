# Etapa 02 (prompt do usuário) — Data Exploration & Engineering

Contexto: o motor de scoring já existia (construído na etapa anterior). Esta etapa acrescentou a camada de dados e a análise documentada, sem mudar o scoring.

## O que foi feito
- `src/data_processing.py`: lê sem alterar os brutos (teste com SHA-256), valida chaves primárias e estrangeiras, faz joins com `validate="many_to_one"`, reconcilia contagens, aplica política explícita de nulos, declara o papel de cada coluna e grava o log de qualidade.
- `src/exploratory_analysis.py`: conversão com IC de Wilson, qui-quadrado por permutação, AUC em holdout temporal, snapshots point-in-time, vieses.
- 13 testes de integridade; 30 no total.
- Teste de consistência entre o loader do app e o pipeline, para que as correções de dados não divirjam.

## Erros encontrados durante a etapa
| Erro | Como apareceu | Correção |
|---|---|---|
| A checagem de espaços contava nulos como "alterados" (NaN ≠ NaN) e gerou 4 falsos alertas (até 2.089 linhas) | Leitura do log de qualidade na primeira execução | Comparação só entre valores presentes |
| No rascunho do doc 04: "77% dos deals nos EUA", "jul/2017 34% vs 8–19%", "79 deals por conta" | Conferência de cada número com o código antes de publicar | Valores reais: 83%; jul 34% e ago 32% vs 8–21%; 87 deals por conta |

## Descobertas novas desta etapa
- Conta ausente só ocorre em deals abertos: seria vazamento se usada como preditor.
- Truncamento à esquerda: não há fechamentos antes de 01/03/2017, o que explica o win rate de 81–82% dos deals engajados em 2016.
- A diferença entre vendedores é compatível com acaso: desvio-padrão de 0,037 contra 0,033 esperado; IC 95% contém a média em 28 de 30 vendedores.
- Sinais de dados sintéticos: ciclo mediano de 8–9 dias nos meses de início de trimestre e datas uniformes em todos os dias da semana.
