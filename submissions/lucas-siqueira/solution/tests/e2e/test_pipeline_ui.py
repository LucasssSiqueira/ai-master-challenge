"""Testes ponta a ponta da tabela de deals, no navegador real.

Rodam só quando há um servidor e o Playwright instalado:
    streamlit run app.py
    LEAD_SCORER_URL=http://localhost:8501 python -m pytest tests/e2e
Os valores esperados vêm do mesmo motor de score que o app usa (nada é fixado à mão).
"""
import os
from urllib.parse import quote

import pytest

pytest.importorskip("playwright")
from playwright.sync_api import sync_playwright  # noqa: E402

from lead_scorer.data_loader import load_deals  # noqa: E402
from lead_scorer.scoring import build_priority_list  # noqa: E402

URL = os.environ.get("LEAD_SCORER_URL")
pytestmark = pytest.mark.skipif(not URL, reason="defina LEAD_SCORER_URL para rodar os testes no navegador")


@pytest.fixture(scope="module")
def pipeline():
    df, _ = build_priority_list(load_deals())
    df["band"] = df["band"].astype(str)
    return df


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as p:
        b = p.chromium.launch(channel=os.environ.get("PW_CHANNEL", "chrome"), headless=True)
        yield b
        b.close()


def open_table(browser, query: str, width: int = 1440, height: int = 1000):
    page = browser.new_page(viewport={"width": width, "height": height})
    errors = []
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.goto(f"{URL}/{query}")
    frame = page.wait_for_selector("iframe", timeout=60000).content_frame()
    frame.wait_for_selector("#range", timeout=60000)
    frame.wait_for_function("document.querySelector('#count').textContent.length > 0")
    return page, frame, errors


def ids(frame):
    return frame.eval_on_selector_all(".body .row", "rs => rs.map(r => r.dataset.id)")


CENTRAL = "?page=pipeline&scope=" + quote("Região") + "&who=Central"


def test_default_order_and_count_match_the_engine(browser, pipeline):
    page, f, errors = open_table(browser, CENTRAL)
    expected = pipeline[(pipeline["regional_office"] == "Central") & (pipeline["band"] != "Requalificar")]
    assert f.inner_text("#count") == f"{len(expected)} deals ativos · Central"
    assert ids(f) == expected["opportunity_id"].head(50).tolist()
    assert errors == []
    page.close()


def test_search_filters_and_reset(browser, pipeline):
    page, f, _ = open_table(browser, CENTRAL)
    central = pipeline[(pipeline["regional_office"] == "Central") & (pipeline["band"] != "Requalificar")]
    f.fill("#q", "hatfan")
    hatfan = central[central["account"].fillna("").str.lower().str.contains("hatfan")]
    assert f.inner_text("#count").startswith(f"{len(hatfan)} de {len(central)}")
    assert set(ids(f)) == set(hatfan["opportunity_id"])

    # Filtros combinados: busca + vendedor + etapa.
    seller = hatfan["sales_agent"].iloc[0]
    f.click('[data-menu="sellers"]')
    f.click(f'.opt[data-value="{seller}"]')
    f.click('[data-menu="stages"]')
    f.click('.opt[data-value="Prospecção"]')
    combo = hatfan[(hatfan["sales_agent"] == seller) & (hatfan["deal_stage"] == "Prospecting")]
    assert set(ids(f)) == set(combo["opportunity_id"])
    assert f.is_visible("#clear")

    # Estado vazio e reset em um clique.
    f.fill("#q", "zzzz-nao-existe")
    assert f.is_visible(".empty")
    f.click("#clear2")
    assert f.inner_text("#count") == f"{len(central)} deals ativos · Central"
    assert not f.is_visible("#clear")
    page.close()


def test_priority_filter_keeps_the_selected_sort(browser, pipeline):
    page, f, _ = open_table(browser, "?page=pipeline&scope=Time+todo")
    f.click('[data-menu="sort"]')
    f.click('.opt[data-sort="value"]')
    f.click('[data-menu="priorities"]')
    f.click('.opt[data-value="Alta prioridade"]')
    alta = pipeline[pipeline["band"] == "Alta"]
    # Valor decrescente, empates na ordem padrão (estável).
    expected = alta.assign(r=range(len(alta))).sort_values(["sales_price", "r"], ascending=[False, True])
    assert ids(f) == expected["opportunity_id"].head(50).tolist()
    assert "ordenado por valor" in f.inner_text("#range")
    page.close()


@pytest.mark.parametrize("sort, column, high_first", [("score", "score", True), ("age", "age_days", True)])
def test_header_sort_and_toggle(browser, pipeline, sort, column, high_first):
    page, f, _ = open_table(browser, "?page=pipeline&scope=Vendedor&who=" + quote("Maureen Marcano"))
    data = pipeline[(pipeline["sales_agent"] == "Maureen Marcano") & (pipeline["band"] != "Requalificar")]
    data = data.assign(r=range(len(data)))
    f.click(f'.hdr [data-sort="{sort}"]')
    expected = data.sort_values([column, "r"], ascending=[not high_first, True], na_position="last")
    assert ids(f) == expected["opportunity_id"].tolist()
    assert f.get_attribute(f'.hdr [data-sort="{sort}"]', "aria-sort") == "descending"
    f.click(f'.hdr [data-sort="{sort}"]')
    assert f.get_attribute(f'.hdr [data-sort="{sort}"]', "aria-sort") == "ascending"
    page.close()


def test_drawer_shows_the_real_deal_and_keeps_context(browser, pipeline):
    page, f, _ = open_table(browser, CENTRAL)
    f.click("#next")
    f.eval_on_selector("#grid", "g => g.scrollTop = 400")
    row = f.query_selector(".body .row:nth-child(12)")
    deal_id = row.get_attribute("data-id")
    row.click()
    f.wait_for_selector(".drawer.open")
    deal = pipeline.set_index("opportunity_id").loc[deal_id]
    text = f.inner_text(".drawer")
    assert str(deal["score"]) in text and deal["action"] in text and deal["product"] in text
    for reason in deal["reasons"]:
        assert reason.split(" ", 1)[1] in text

    page.keyboard.press("Escape")
    f.wait_for_selector(".drawer:not(.open)")
    assert "51–100" in f.inner_text("#range")
    assert f.eval_on_selector("#grid", "g => g.scrollTop") > 300
    row.click()
    f.click("#close")
    f.wait_for_selector(".drawer:not(.open)")
    page.close()


def test_deep_link_opens_the_drawer(browser):
    page, f, _ = open_table(
        browser, "?page=pipeline&scope=Vendedor&who=" + quote("Maureen Marcano") + "&deal=T7N0RX05"
    )
    f.wait_for_selector(".drawer.open")
    assert "T7N0RX05" in f.inner_text(".drawer")
    page.close()


def test_score_tooltip_explains_the_factors(browser, pipeline):
    page, f, _ = open_table(browser, "?page=pipeline&scope=Vendedor&who=" + quote("Maureen Marcano"))
    first = pipeline[pipeline["sales_agent"] == "Maureen Marcano"].iloc[0]
    f.hover(".body .row:first-child .c-score")
    f.wait_for_selector(".tip.show")
    tip = f.inner_text(".tip")
    assert f"{round(first['score_value'])} de 60" in tip and f"{round(first['score_timing'])} de 40" in tip
    page.close()


@pytest.mark.parametrize("width", [1440, 1100, 900, 390])
def test_nothing_is_cut_at_any_width(browser, width):
    page, f, _ = open_table(browser, CENTRAL, width=width, height=900)
    overflow = f.evaluate("""() => {
        const doc = document.documentElement;
        const cells = [...document.querySelectorAll('.body .row:first-child .c')]
            .filter(c => getComputedStyle(c).display !== 'none');
        const row = document.querySelector('.body .row');
        const visible = sel => [...document.querySelectorAll(sel)].filter(c => getComputedStyle(c).display !== 'none')
            .map(c => [...c.classList].find(k => k.startsWith('c-')));
        const hdr = document.querySelector('.hdr');
        return {page: doc.scrollWidth - doc.clientWidth, grid: document.querySelector('#grid').scrollWidth - document.querySelector('#grid').clientWidth,
                outside: cells.filter(c => c.getBoundingClientRect().right > row.getBoundingClientRect().right + 1).length,
                // Cabeçalho e linhas com as mesmas colunas visíveis (quando o cabeçalho aparece).
                aligned: getComputedStyle(hdr).display === 'none' ||
                         JSON.stringify(visible('.hdr .c')) === JSON.stringify(visible('.body .row:first-child .c'))};
    }""")
    assert overflow == {"page": 0, "grid": 0, "outside": 0, "aligned": True}
    page.close()


def test_stale_page_sorts_by_value_without_priority_filter(browser, pipeline):
    page, f, _ = open_table(browser, "?page=requalify&scope=Vendedor&who=" + quote("Anna Snelling"))
    stale = pipeline[(pipeline["sales_agent"] == "Anna Snelling") & (pipeline["band"] == "Requalificar")]
    stale = stale.sort_values("sales_price", ascending=False, kind="stable")
    assert ids(f) == stale["opportunity_id"].head(50).tolist()
    assert not f.query_selector('[data-menu="priorities"]')
    assert f.inner_text("#count").startswith(f"{len(stale)} deals há mais de 138 dias")
    page.close()
