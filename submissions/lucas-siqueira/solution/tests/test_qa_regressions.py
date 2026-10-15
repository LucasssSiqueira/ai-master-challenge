"""Regressões dos problemas encontrados na auditoria (docs/08-quality-assurance.md)."""
import dataclasses
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from lead_scorer.config import DEFAULT_CONFIG
from lead_scorer.data_loader import load_deals
from lead_scorer.scoring import build_priority_list, history_stats, timing_points

PAST = pd.Timestamp("2017-06-30")


@pytest.fixture(scope="module")
def deals():
    return load_deals()


@pytest.fixture(scope="module")
def scored(deals):
    return build_priority_list(deals)


@pytest.fixture(scope="module")
def scored_past(deals):
    return build_priority_list(deals, dataclasses.replace(DEFAULT_CONFIG, reference_date=PAST))


# QA-03 (P1): data de referência anterior não pode usar o futuro.
def test_past_reference_uses_only_history_known_at_that_date(deals, scored_past):
    _, stats = scored_past
    known = deals[deals["close_date"] <= PAST]
    assert stats.base_win_rate == pytest.approx(known["is_won"].mean())
    assert stats.rates["n_closed"].sum() == len(known)


def test_past_reference_lists_deals_as_they_were(deals, scored_past):
    df, _ = scored_past
    engaged_then = deals["engage_date"].notna() & (deals["engage_date"] <= PAST)
    open_then = engaged_then & (deals["close_date"].isna() | (deals["close_date"] > PAST))
    never_engaged = deals["engage_date"].isna()
    assert len(df) == open_then.sum() + never_engaged.sum()
    assert (df["age_days"].dropna() >= 0).all()
    assert set(df["deal_stage"]) == {"Engaging", "Prospecting"}
    assert df["close_value"].isna().all() and df["close_date"].isna().all()


def test_default_reference_is_unchanged(scored):
    df, _ = scored
    assert len(df) == 2089
    assert (df["band"] == "Requalificar").sum() == 1291


# QA-05 (P2): o texto de valor dá a posição real no catálogo.
@pytest.mark.parametrize("product, text", [
    ("GTK 500", "o mais caro dos 7 produtos"),
    ("MG Advanced", "o 4º mais caro dos 7 produtos"),
    ("MG Special", "o mais barato dos 7 produtos"),
])
def test_value_reason_states_real_price_rank(scored, product, text):
    df, _ = scored
    reasons = df.loc[df["product"] == product, "reasons"].iloc[0]
    assert any(text in r for r in reasons)
    assert not any("entre os produtos" in r for r in reasons)


# QA-06 (P2): possíveis duplicatas são sinalizadas ao vendedor.
def test_possible_duplicates_are_flagged(scored):
    df, _ = scored
    flagged = df["reasons"].map(lambda rs: any("Possível duplicata" in r for r in rs))
    # 12 pares entre abertos + 1 aberto cujo "gêmeo" já fechou.
    assert flagged.sum() == df["possible_duplicate"].sum() == 13


# QA-04 (P2): faixas seguem a regra documentada (percentis com empates para cima).
def test_bands_follow_documented_percentile_rule(scored):
    df, _ = scored
    active = df[df["band"].isin(["Alta", "Média", "Baixa"])]
    high = active["score"].quantile(DEFAULT_CONFIG.high_quantile)
    medium = active["score"].quantile(DEFAULT_CONFIG.medium_quantile)
    expected = np.where(active["score"] >= high, "Alta", np.where(active["score"] >= medium, "Média", "Baixa"))
    assert (active["band"].astype(str).to_numpy() == expected).all()


# QA-08 (P3): histórico degenerado falha com mensagem clara; quantis iguais não geram divisão por zero.
def test_history_without_wins_raises_clear_error(deals):
    only_lost = deals[deals["deal_stage"] == "Lost"]
    with pytest.raises(ValueError, match="deal ganho"):
        history_stats(only_lost, deals.drop_duplicates("product")["sales_price"], DEFAULT_CONFIG)


def test_timing_handles_coincident_quantiles(scored):
    _, stats = scored
    flat = dataclasses.replace(stats, won_p25=0.0, won_p75=138.0, won_p95=138.0)
    pts = timing_points(pd.Series([0, 50, 138, 139], dtype=float), flat, DEFAULT_CONFIG)
    assert np.isfinite(pts).all() and pts.between(0, DEFAULT_CONFIG.weight_timing).all()


# QA-07 (P1): as versões mínimas aceitas precisam funcionar juntas.
def test_requirements_pin_numpy_2_and_compatible_pandas():
    reqs = (Path(__file__).resolve().parent.parent / "requirements.txt").read_text()
    assert "numpy>=2.0" in reqs
    assert "pandas>=2.2.2" in reqs
    assert "streamlit>=1.49" in reqs  # 1.46–1.48 não aceitam width="stretch" em st.dataframe
