# Etapa 02 — Implementação (Claude Code)

Decisões aprovadas antes de codar: Streamlit, pesos 50/30/20, data de referência 31/12/2017, faixa Requalificar acima de 138 dias.

## Ordem de construção
1. `data_loader` com validação que falha alto (produto sem preço, vendedor sem time).
2. `scoring` + `explain`, conferidos por amostra de saída antes dos testes.
3. 15 testes (pytest).
4. `backtest` point-in-time (snapshots mensais de 2017).
5. `app.py`, verificado no navegador: visões Vendedor, Manager, Região e Time todo; seleção de linha; abas.
6. Instalação limpa em venv novo: testes verdes e app sem exceções (Streamlit AppTest).

## Problemas encontrados e corrigidos
| Problema | Como apareceu | Correção |
|---|---|---|
| O #1 do "foco da semana" da Anna Snelling era um MG Special de US$ 55 (faixa Baixa), à frente de Prospecting de US$ 5.482 | Inspeção visual no navegador | Ordem das faixas passou a ser Alta → Média → Qualificar → Baixa → Requalificar |
| O eixo do gráfico de ciclo era ordenado como texto (0–2, 10–12, 12–14, 2–4…) | Inspeção visual | Índice numérico por semana |
| Os KPIs truncavam em telas estreitas ("US$ 123….") | Visão Manager no painel estreito | Formato compacto (US$ 123 mil) |
| O delta "↑ 56 deals" sugeria crescimento | Inspeção visual | Contagem movida para o rótulo |
| O README dizia que "metade dos vendedores" não tinha deal ativo | Conferência do número antes de publicar | Valor real: 6 de 27 |

## Resultado honesto do backtest
- Top 20% do score: 46% do valor ganho. Ordenar só por valor: 49%. Ordem aleatória: 20%.
- AUC da Chance: 0,50. AUC do score total: 0,50.
- Conclusão: os dados não permitem prever Won/Lost. O ganho do score está na separação dos deals parados, no momento e na ação por deal, não em predição. O app e o README dizem isso explicitamente.

## Revisão dos pesos (pedido do usuário após o backtest)
- Grid de 9 combinações. A chance (AUC 0,50) só reduzia a captura de valor.
- Adotado 60/40/0: captura de 45,6% → 48,3%, maior em 8 de 9 meses. Correlação com "só valor" de 0,75, a menor entre as opções com captura alta.
- A chance continua visível nos motivos, com o aviso ℹ️ "Informativo, não entra no score".
- Testes novos: pesos padrão, chance sem peso no score, motivo informativo presente em todos os deals. 17 testes passando.
