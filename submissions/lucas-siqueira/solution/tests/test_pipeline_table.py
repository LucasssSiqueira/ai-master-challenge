"""Dados entregues à tabela interativa: fiéis ao motor de score e seguros para embutir no HTML."""
import json
import re

import pytest

from lead_scorer.data_loader import load_deals
from lead_scorer.scoring import build_priority_list
from ui import pipeline_table as pt


@pytest.fixture(scope="module")
def pipeline():
    df, _ = build_priority_list(load_deals())
    df["band"] = df["band"].astype(str)
    return df


def render(df, **overrides):
    kwargs = dict(title="Pipeline", noun=["deal ativo", "deals ativos"], scope_label="Central", show_seller=True,
                  show_priority=True, default_sort="priority", initial_deal=None, weights=(60.0, 40.0))
    kwargs.update(overrides)
    return pt.render(df, **kwargs)


def embedded(html: str, name: str):
    return json.loads(re.search(rf"const {name} = (.*?);\n", html).group(1).replace("<\\/", "</"))


def test_records_preserve_engine_values_and_order(pipeline):
    active = pipeline[pipeline["band"] != "Requalificar"]
    recs = pt.records(active)
    assert [r["id"] for r in recs] == active["opportunity_id"].tolist()
    assert [r["rank"] for r in recs] == list(range(len(active)))
    for rec, (_, row) in zip(recs[:200], active.head(200).iterrows()):
        assert rec["score"] == row["score"] and rec["value"] == row["sales_price"]
        assert rec["action"] == row["action"] and rec["short"] == row["short_reason"]
        assert len(rec["reasons"]) == len(row["reasons"])
        assert rec["priority"] == pt.PRIORITY_LABELS[row["band"]]


def test_missing_values_are_explicit(pipeline):
    recs = {r["id"]: r for r in pt.records(pipeline)}
    prospect = pipeline[pipeline["deal_stage"] == "Prospecting"].iloc[0]
    no_account = pipeline[pipeline["account"].isna()].iloc[0]
    assert recs[prospect["opportunity_id"]]["age"] is None
    assert recs[prospect["opportunity_id"]]["stage"] == "Prospecção"
    assert recs[no_account["opportunity_id"]]["account"] is None and recs[no_account["opportunity_id"]]["crm"]


def test_data_cannot_break_out_of_the_script(pipeline):
    df = pipeline.head(3).copy()
    df.loc[df.index[0], "account"] = '</script><img src=x onerror="alert(1)">'
    html = render(df)
    script = html[html.index("<script>"):]
    assert script.count("</script>") == 1  # só o fechamento real
    assert embedded(html, "DATA")[0]["account"] == '</script><img src=x onerror="alert(1)">'


def test_config_reflects_the_scope(pipeline):
    central = pipeline[(pipeline["regional_office"] == "Central") & (pipeline["band"] != "Requalificar")]
    cfg = embedded(render(central, initial_deal="ABC"), "CFG")
    assert cfg["sellers"] == sorted(central["sales_agent"].unique())
    assert cfg["priorities"] == [pt.PRIORITY_LABELS[b] for b in ["Alta", "Média", "Qualificar", "Baixa"]
                                 if b in set(central["band"])]
    assert set(cfg["stages"]) <= {"Em negociação", "Prospecção"}
    assert cfg["initialDeal"] == "ABC" and cfg["weights"] == [60.0, 40.0]


def test_stale_mode_has_no_priority_filter(pipeline):
    stale = pipeline[pipeline["band"] == "Requalificar"]
    cfg = embedded(render(stale, show_priority=False, default_sort="value"), "CFG")
    assert cfg["showPriority"] is False and cfg["defaultSort"] == "value"
    assert cfg["priorities"] == ["Parado"]
