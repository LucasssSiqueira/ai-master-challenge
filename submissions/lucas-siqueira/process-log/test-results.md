# Resultados dos testes — auditoria final (15/10/2026)

Execução feita como um avaliador faria: **clone novo** da branch `submission/lucas-siqueira` do GitHub (commit `cdd24fe`), **venv novo** com Python 3.11 e só os comandos do README.

## Ambiente
- macOS, Python 3.11.
- `pip install -r requirements.txt` resolveu pandas 3.0.6, numpy 2.4.6, streamlit 1.66.0 e pytest 9.1.1.
- As versões **mínimas** (pandas 2.2.2, numpy 2.0.0, streamlit 1.49.0) foram testadas na Etapa 05 e no redesign do Pipeline ([doc 08](../docs/08-quality-assurance.md), [doc 10](../docs/10-pipeline-ux.md)).

## Resultados

| Comando | Resultado |
|---|---|
| `python -m pytest` | **64 passed, 1 skipped**. O skip é o módulo `tests/e2e`, pulado de propósito sem Playwright |
| `python -m lead_scorer.backtest` | Captura nos top 20%: score 0,483, só valor 0,494, aleatória 0,198; AUC chance 0,496, AUC score 0,502 (iguais aos números do README) |
| `python -m src.data_processing` | Tabela analítica com 8.800 linhas × 30 colunas; nenhum arquivo versionado alterado (`git status` limpo) |
| `streamlit run app.py` | Servidor no ar (`/_stcore/health` → `ok`), sem erros no log |
| AppTest: 4 páginas × todos os escopos e pessoas | 113 execuções, 0 falhas |
| `LEAD_SCORER_URL=… pytest tests/e2e` (Playwright + Chrome) | 4 execuções: **1ª com 1 falha em 13** (12 passed), 2ª, 3ª e 4ª com **13 passed**. A 3ª e a 4ª foram com o servidor reiniciado a frio |

## Falha intermitente (não resolvida)
Na 1ª execução, um dos 13 testes no navegador falhou. A rodada levou 120 s, contra 41–58 s nas demais. A mensagem de erro não foi guardada e a falha não se repetiu em 3 novas execuções, então **a causa não foi identificada**. A hipótese mais provável, **não confirmada**, é tempo de carregamento na primeira abertura. Se repetir, rodar com `-rf` para registrar qual teste falha.
