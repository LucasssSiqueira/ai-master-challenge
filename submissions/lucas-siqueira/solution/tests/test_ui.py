"""Testes da camada de interface: insights, textos curtos e blocos de HTML."""
import pandas as pd
import pytest

from lead_scorer import insights
from lead_scorer.config import DEFAULT_CONFIG
from lead_scorer.data_loader import load_deals
from lead_scorer.explain import money_short
from lead_scorer.scoring import BAND_ORDER, build_priority_list
from ui import components as ui


@pytest.fixture(scope="module")
def scored():
    df, stats = build_priority_list(load_deals())
    df["band"] = df["band"].astype(str)
    return df, stats


def seller(df, name="Maureen Marcano"):
    return df[df["sales_agent"] == name]


@pytest.mark.parametrize("value, text", [(55, "US$ 55"), (40823, "US$ 41 mil"), (3198664, "US$ 3,2 mi")])
def test_money_short(value, text):
    assert money_short(value) == text


def test_short_reason_matches_timing_segment(scored):
    df, _ = scored
    expected = {"stale": "Parado há", "not_engaged": "Ainda não engajado", "window": "dentro da janela",
                "late": "saindo da janela", "very_late": "saindo da janela"}
    for seg, text in expected.items():
        rows = df[df["timing_segment"] == seg]
        assert len(rows) and rows["short_reason"].str.contains(text).all(), seg


def test_priorities_are_the_top_non_stale_deals(scored):
    df, _ = scored
    top = insights.priorities(seller(df))
    assert len(top) == 5
    assert "Requalificar" not in set(top["band"])
    assert top["score"].tolist() == [85, 82, 80, 70, 69]


def test_headline_sums_the_priorities(scored):
    df, _ = scored
    top = insights.priorities(seller(df))
    assert insights.headline(seller(df)) == (
        f"O Lead Scorer encontrou {money_short(top['sales_price'].sum())} em 5 deals que precisam de você hoje."
    )
    assert "Nenhum deal ativo" in insights.headline(df[df["band"] == "Requalificar"])


def test_main_insight_points_to_stale_value_when_it_dominates(scored):
    df, _ = scored
    d = seller(df)
    stale_share = d.loc[d["band"] == "Requalificar", "sales_price"].sum() / d["sales_price"].sum()
    insight = insights.main_insight(d, DEFAULT_CONFIG.stale_days)
    assert insight.metric == f"{stale_share:.0%}" == "71%"
    assert insight.page == "requalify"


def test_main_insight_falls_back_when_pipeline_is_clean(scored):
    df, _ = scored
    clean = df[df["band"] != "Requalificar"]
    insight = insights.main_insight(clean, DEFAULT_CONFIG.stale_days)
    assert insight.page == "pipeline"
    assert insight.metric.rstrip("%").isdigit()


def test_band_summary_covers_every_band_in_order(scored):
    df, _ = scored
    summary = insights.band_summary(seller(df))
    assert list(summary.index) == BAND_ORDER
    assert summary["deals"].sum() == len(seller(df))
    assert summary["share"].sum() == pytest.approx(1.0)


def test_html_escapes_data(scored):
    df, _ = scored
    row = seller(df).iloc[0].copy()
    row["account"] = '<script>alert("x")</script>'
    html = ui.detail_card(row, [("Valor", 10, 60)])
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_html_is_single_line_for_markdown(scored):
    df, _ = scored
    d = seller(df)
    blocks = [
        ui.overview_card(d, insights.band_summary(d)),
        ui.health_card(insights.band_summary(d), insights.active_share(d)),
        ui.priorities_card(insights.priorities(d), {"scope": "Vendedor", "who": "Maureen Marcano"}),
        ui.insight_card(insights.main_insight(d, 138), {"scope": "Vendedor"}),
    ]
    for html in blocks:
        assert "\n" not in html and "\n\n" not in html


def test_priority_links_keep_scope_and_open_the_deal(scored):
    df, _ = scored
    top = insights.priorities(seller(df))
    html = ui.priorities_card(top, {"page": "overview", "scope": "Vendedor", "who": "Maureen Marcano"})
    first = top.iloc[0]["opportunity_id"]
    assert f"?page=pipeline&amp;scope=Vendedor&amp;who=Maureen+Marcano&amp;deal={first}" in html
    assert html.count('aria-label="Abrir deal') == 5


def test_rail_marks_only_the_active_page():
    html = ui.rail("requalify", {"scope": "Vendedor", "who": "Anna Snelling"})
    assert html.count('class="active"') == 1
    assert 'title="Deals parados" class="active"' in html


def test_reason_prefixes_become_dots():
    color, text = ui.split_reason("⚠️ Conta não informada")
    assert text == "Conta não informada" and color.startswith("#")


def test_date_label_in_portuguese():
    assert ui.date_label(pd.Timestamp("2017-12-31")) == "domingo, 31 de dezembro de 2017"


@pytest.mark.parametrize("scope, who, expected", [
    ("Vendedor", "Maureen Marcano", "Maureen"),
    ("Manager", "Cara Losch", "Cara"),
    ("Região", "West", "Lucas"),
    ("Time todo", None, "Lucas"),
])
def test_greeting_uses_the_person_in_focus(scope, who, expected):
    assert ui.greeting_name(scope, who, "Lucas") == expected
