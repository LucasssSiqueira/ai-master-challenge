import dataclasses

import pandas as pd
import pytest

from lead_scorer.config import DEFAULT_CONFIG
from lead_scorer.data_loader import load_deals
from lead_scorer.scoring import build_priority_list, prob_points, timing_points, value_points


@pytest.fixture(scope="module")
def scored():
    return build_priority_list(load_deals())


def test_every_open_deal_is_scored_and_explained(scored):
    df, _ = scored
    assert len(df) == 2089
    assert df["score"].between(0, 100).all()
    assert df["band"].notna().all()
    assert (df["reasons"].str.len() >= 2).all()
    assert df["action"].str.len().gt(0).all()


def test_stale_deals_go_to_requalify(scored):
    df, _ = scored
    stale = df["deal_stage"].eq("Engaging") & (df["age_days"] > DEFAULT_CONFIG.stale_days)
    assert (df.loc[stale, "band"] == "Requalificar").all()
    assert (df.loc[~stale & df["deal_stage"].eq("Engaging"), "band"] != "Requalificar").all()


def test_prospecting_goes_to_qualify(scored):
    df, _ = scored
    assert (df.loc[df["deal_stage"].eq("Prospecting"), "band"] == "Qualificar").all()


def test_score_is_not_just_sorting_by_value(scored):
    df, _ = scored
    active = df[df["band"].isin(["Alta", "Média", "Baixa"])]
    spearman = active["score"].rank().corr(active["sales_price"].rank())
    assert spearman < 0.95
    # Existe deal mais barato com score maior que um deal mais caro.
    assert not active.sort_values(["sales_price", "score"])["score"].is_monotonic_increasing


def test_short_high_priority_list_per_agent(scored):
    df, _ = scored
    assert df[df["band"] == "Alta"].groupby("sales_agent").size().max() <= 15


def test_value_points_are_monotonic_and_bounded(scored):
    _, stats = scored
    prices = pd.Series([55, 550, 1096, 3393, 4821, 5482, 26768])
    pts = value_points(prices, stats, DEFAULT_CONFIG)
    assert pts.is_monotonic_increasing
    assert pts.iloc[0] == 0 and pts.iloc[-1] == DEFAULT_CONFIG.weight_value


def test_timing_boundaries(scored):
    _, stats = scored
    ages = pd.Series([None, 0, stats.won_p25, stats.won_p75, stats.won_p95, 138, 139], dtype=float)
    pts = timing_points(ages, stats, DEFAULT_CONFIG)
    w = DEFAULT_CONFIG.weight_timing
    assert pts.iloc[0] == 0  # Prospecting: sem data
    assert pts.iloc[1] == pytest.approx(w / 2)
    assert pts.iloc[2] == pts.iloc[3] == w  # janela típica dos ganhos
    assert pts.iloc[4] == pytest.approx(w / 2)
    assert pts.iloc[5] == pytest.approx(0)
    assert pts.iloc[6] == 0  # além do maior ciclo já visto


def test_average_rep_gets_half_the_probability_points_when_weighted(scored):
    _, stats = scored
    cfg = dataclasses.replace(DEFAULT_CONFIG, weight_prob=20.0)
    pts = prob_points(pd.Series([stats.base_win_rate, 0.0, 1.0]), stats, cfg)
    assert pts.tolist() == [10, 0, 20]


def test_default_weights_follow_backtest_decision():
    cfg = DEFAULT_CONFIG
    assert (cfg.weight_value, cfg.weight_timing, cfg.weight_prob) == (60, 40, 0)


def test_chance_is_shown_but_not_scored(scored):
    df, _ = scored
    assert (df["score_prob"] == 0).all()
    assert (df["score"] == (df["score_value"] + df["score_timing"]).round()).all()
    chance = df["reasons"].map(lambda rs: [r for r in rs if "Chance estimada" in r])
    assert chance.map(len).eq(1).all()
    assert chance.map(lambda rs: rs[0].startswith("ℹ️") and "não entra no score" in rs[0]).all()


def test_shrinkage_pulls_small_samples_to_the_mean(scored):
    _, stats = scored
    small = stats.rates[stats.rates["n_closed"] <= 5]
    assert (small["win_rate"] - stats.base_win_rate).abs().max() < 0.05
