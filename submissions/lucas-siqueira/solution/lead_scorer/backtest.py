"""Validação point-in-time: o score teria ajudado nos meses de 2017?

Para cada fim de mês `s`, reconstrói os deals que estavam abertos (engajados até `s` e
fechados depois), pontua usando só o histórico fechado até `s` e compara com o desfecho.
Limitação: só entram deals que depois fecharam (os abertos hoje não têm desfecho).

Uso: python -m lead_scorer.backtest
"""
import numpy as np
import pandas as pd

from .config import DEFAULT_CONFIG, ScoringConfig
from .data_loader import load_deals
from .scoring import score_open_deals

SNAPSHOTS = pd.date_range("2017-03-31", "2017-11-30", freq="ME")
TOP_SHARE = 0.20


def auc(won: pd.Series, score: pd.Series) -> float:
    """Probabilidade de um deal ganho ter score maior que um perdido (0,5 = acaso)."""
    ranks = score.rank().to_numpy()
    won = won.to_numpy().astype(bool)
    n_won, n_lost = won.sum(), (~won).sum()
    return float((ranks[won].sum() - n_won * (n_won + 1) / 2) / (n_won * n_lost))


def won_value_captured(df: pd.DataFrame, by: pd.Series) -> float:
    """Fração do valor ganho que estava nos top 20% da lista ordenada por `by`."""
    n_top = max(1, int(len(df) * TOP_SHARE))
    top = by.sort_values(ascending=False).index[:n_top]
    won_value = df["close_value"].where(df["is_won"], 0)
    return float(won_value.loc[top].sum() / won_value.sum())


def run_backtest(deals: pd.DataFrame, cfg: ScoringConfig = DEFAULT_CONFIG) -> pd.DataFrame:
    catalog_prices = deals.drop_duplicates("product")["sales_price"]
    closed = deals[deals["deal_stage"].isin(["Won", "Lost"])]
    rows = []
    for snap in SNAPSHOTS:
        history = closed[closed["close_date"] <= snap]
        open_then = closed[(closed["engage_date"] <= snap) & (closed["close_date"] > snap)]
        scored, _ = score_open_deals(open_then, history, catalog_prices, snap, cfg)
        scored.index = open_then.index
        random_capture = np.mean([
            won_value_captured(scored, pd.Series(np.random.default_rng(seed).random(len(scored)), index=scored.index))
            for seed in range(20)
        ])
        rows.append({
            "snapshot": snap.date(),
            "deals_abertos": len(scored),
            "win_rate": scored["is_won"].mean(),
            "auc_chance": auc(scored["is_won"], scored["win_rate"]),
            "auc_score": auc(scored["is_won"], scored["score"]),
            "captura_score": won_value_captured(scored, scored["score"]),
            "captura_so_valor": won_value_captured(scored, scored["sales_price"]),
            "captura_aleatoria": random_capture,
        })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    result = run_backtest(load_deals())
    pd.set_option("display.width", 160)
    print(result.round(3).to_string(index=False))
    print("\nMédia:")
    print(result.drop(columns="snapshot").mean().round(3).to_string())
