"""Priority Score = Valor + Momento + Chance (pesos em config.py), mais a faixa de ação.

O score é uma regra de priorização, não uma probabilidade calibrada: no histórico,
nenhum atributo disponível (vendedor, produto, conta, setor, região) separa Won de
Lost melhor que o acaso. Por isso o peso padrão da chance é zero: ela é calculada e
mostrada ao vendedor, mas não muda a ordem.
"""
from dataclasses import dataclass

import numpy as np
import pandas as pd

from . import explain
from .config import DEFAULT_CONFIG, ScoringConfig

# Ordem de atenção: um Prospecting a qualificar merece mais tempo que um deal de prioridade baixa.
BAND_ORDER = ["Alta", "Média", "Qualificar", "Baixa", "Requalificar"]


@dataclass(frozen=True)
class HistoryStats:
    """O que o histórico de deals fechados diz, usado no score e nas explicações."""

    base_win_rate: float
    won_p25: float
    won_p75: float
    won_p95: float
    stale_days: int
    lost_median: float
    min_price: float
    max_price: float
    rates: pd.DataFrame  # sales_agent, product, n_closed, win_rate (com shrinkage)


def history_stats(history: pd.DataFrame, catalog_prices: pd.Series, cfg: ScoringConfig) -> HistoryStats:
    closed = history[history["deal_stage"].isin(["Won", "Lost"])]
    if closed.empty:
        raise ValueError("é preciso ao menos um deal fechado para calcular o histórico")
    won_cycle = closed.loc[closed["is_won"], "cycle_days"]
    base = float(closed["is_won"].mean())

    grouped = closed.groupby(["sales_agent", "product"])["is_won"].agg(wins="sum", n_closed="count").reset_index()
    grouped["win_rate"] = (grouped["wins"] + cfg.k_shrinkage * base) / (grouped["n_closed"] + cfg.k_shrinkage)

    return HistoryStats(
        base_win_rate=base,
        won_p25=float(won_cycle.quantile(0.25)),
        won_p75=float(won_cycle.quantile(0.75)),
        won_p95=float(won_cycle.quantile(0.95)),
        stale_days=cfg.stale_days,
        lost_median=float(closed.loc[~closed["is_won"], "cycle_days"].median()),
        min_price=float(catalog_prices.min()),
        max_price=float(catalog_prices.max()),
        rates=grouped[["sales_agent", "product", "n_closed", "win_rate"]],
    )


def value_points(price: pd.Series, stats: HistoryStats, cfg: ScoringConfig) -> pd.Series:
    """Escala log: o preço varia ~490x; em escala linear o score viraria 'ordenar por valor'."""
    lo, hi = np.log(stats.min_price), np.log(stats.max_price)
    return cfg.weight_value * ((np.log(price) - lo) / (hi - lo)).clip(0, 1)


def timing_segment(age_days: pd.Series, stats: HistoryStats) -> pd.Series:
    conditions = [
        age_days.isna(),
        age_days > stats.stale_days,
        age_days < stats.won_p25,
        age_days <= stats.won_p75,
        age_days <= stats.won_p95,
    ]
    choices = ["not_engaged", "stale", "early", "window", "late"]
    return pd.Series(np.select(conditions, choices, default="very_late"), index=age_days.index)


def timing_points(age_days: pd.Series, stats: HistoryStats, cfg: ScoringConfig) -> pd.Series:
    """Máximo na janela em que deals ganhos costumam fechar; zero depois do maior ciclo já visto.

    Mede o quanto vale agir agora, não a chance de ganhar (a idade não prevê o resultado).
    """
    p25, p75, p95, stale = stats.won_p25, stats.won_p75, stats.won_p95, stats.stale_days
    age = age_days.astype(float)
    factor = np.select(
        [
            age.isna() | (age > stale),
            age < p25,
            age <= p75,
            age <= p95,
        ],
        [
            0.0,
            0.5 + 0.5 * age / p25,
            1.0,
            1.0 - 0.5 * (age - p75) / (p95 - p75),
        ],
        default=0.5 * (stale - age) / (stale - p95),
    )
    return pd.Series(cfg.weight_timing * factor, index=age_days.index)


def prob_points(win_rate: pd.Series, stats: HistoryStats, cfg: ScoringConfig) -> pd.Series:
    """Média do time = metade dos pontos; ±prob_spread de win rate leva a 0 ou ao máximo."""
    half = cfg.weight_prob / 2
    return (half + half * (win_rate - stats.base_win_rate) / cfg.prob_spread).clip(0, cfg.weight_prob)


def score_open_deals(
    open_deals: pd.DataFrame,
    history: pd.DataFrame,
    catalog_prices: pd.Series,
    reference_date: pd.Timestamp,
    cfg: ScoringConfig = DEFAULT_CONFIG,
) -> tuple[pd.DataFrame, HistoryStats]:
    """Componentes numéricos do score. `history` deve conter só o que se sabia em `reference_date`."""
    stats = history_stats(history, catalog_prices, cfg)
    df = open_deals.copy()
    df["age_days"] = (reference_date - df["engage_date"]).dt.days

    df = df.merge(stats.rates, on=["sales_agent", "product"], how="left")
    df["n_closed"] = df["n_closed"].fillna(0).astype(int)
    df["win_rate"] = df["win_rate"].fillna(stats.base_win_rate)

    df["score_value"] = value_points(df["sales_price"], stats, cfg)
    df["score_timing"] = timing_points(df["age_days"], stats, cfg)
    df["score_prob"] = prob_points(df["win_rate"], stats, cfg)
    df["score"] = (df["score_value"] + df["score_timing"] + df["score_prob"]).round().astype(int)
    df["timing_segment"] = timing_segment(df["age_days"], stats)
    return df, stats


def assign_bands(df: pd.DataFrame, cfg: ScoringConfig = DEFAULT_CONFIG) -> pd.Series:
    """A faixa vem antes do score: o score só ordena deals dentro da mesma faixa."""
    band = pd.Series("Baixa", index=df.index, dtype=object)
    active = df["timing_segment"].ne("not_engaged") & df["timing_segment"].ne("stale")
    if active.any():
        high = df.loc[active, "score"].quantile(cfg.high_quantile)
        medium = df.loc[active, "score"].quantile(cfg.medium_quantile)
        band[active & (df["score"] >= high)] = "Alta"
        band[active & (df["score"] < high) & (df["score"] >= medium)] = "Média"
    band[df["timing_segment"].eq("not_engaged")] = "Qualificar"
    band[df["timing_segment"].eq("stale")] = "Requalificar"
    return band


def build_priority_list(deals: pd.DataFrame, cfg: ScoringConfig = DEFAULT_CONFIG) -> tuple[pd.DataFrame, HistoryStats]:
    """Deals abertos pontuados, com faixa, motivos e ação, prontos para a interface."""
    catalog_prices = deals.drop_duplicates("product")["sales_price"]
    df, stats = score_open_deals(
        deals[deals["is_open"]], deals[~deals["is_open"]], catalog_prices, cfg.reference_date, cfg
    )
    df["band"] = pd.Categorical(assign_bands(df, cfg), categories=BAND_ORDER, ordered=True)
    df["needs_crm_fix"] = ~df["has_account"]
    df["reasons"] = [explain.reasons(row, stats, cfg) for row in df.itertuples(index=False)]
    df["action"] = [explain.action(row, stats) for row in df.itertuples(index=False)]
    df = df.sort_values(["band", "score", "sales_price"], ascending=[True, False, False]).reset_index(drop=True)
    return df, stats
