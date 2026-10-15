"""Testes de integridade do pipeline de dados (src/data_processing.py)."""
import hashlib
import shutil

import pandas as pd
import pytest

from lead_scorer.data_loader import load_deals
from src.data_processing import (
    COLUMN_ROLES, EXPECTED_COLUMNS, OUTCOME, RAW_DIR, DataQualityError, load_raw, run,
)


@pytest.fixture(scope="module")
def result():
    return run(out_dir=None)


@pytest.fixture
def raw_copy(tmp_path):
    dest = tmp_path / "raw"
    dest.mkdir()
    for name in EXPECTED_COLUMNS:
        shutil.copy(RAW_DIR / f"{name}.csv", dest / f"{name}.csv")
    return dest


def _digest(directory):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(directory.glob("*.csv"))}


def test_all_tables_loaded_with_expected_columns():
    tables = load_raw()
    assert {n: len(t) for n, t in tables.items()} == {
        "accounts": 85, "products": 7, "sales_teams": 35, "sales_pipeline": 8800,
    }
    for name, columns in EXPECTED_COLUMNS.items():
        assert list(tables[name].columns) == columns


def test_missing_file_is_reported_not_invented(raw_copy):
    (raw_copy / "products.csv").unlink()
    with pytest.raises(FileNotFoundError, match="products"):
        run(raw_copy, out_dir=None)


def test_record_counts_reconcile(result):
    assert result.reconciliation["ok"].all()
    assert len(result.analytic) == 8800
    assert result.analytic["opportunity_id"].is_unique
    assert result.analytic["deal_stage"].value_counts().to_dict() == {
        "Won": 4238, "Lost": 2473, "Engaging": 1589, "Prospecting": 500,
    }


def test_relationships_resolve(result):
    df = result.analytic
    assert df["sales_price"].notna().all()  # todo produto tem preço (GTXPro corrigido)
    assert df["manager"].notna().all()      # todo vendedor tem time
    assert df.loc[~df["account_missing"], "sector"].notna().all()  # toda conta informada existe
    assert "GTXPro" not in set(df["product"])
    assert (result.issues["severity"] != "erro").all()


def test_orphan_foreign_key_stops_the_pipeline(raw_copy):
    pipeline = pd.read_csv(raw_copy / "sales_pipeline.csv")
    pipeline.loc[0, "product"] = "Produto Fantasma"
    pipeline.to_csv(raw_copy / "sales_pipeline.csv", index=False)
    with pytest.raises(DataQualityError, match="chave estrangeira"):
        run(raw_copy, out_dir=None)


def test_duplicate_primary_key_stops_the_pipeline(raw_copy):
    pipeline = pd.read_csv(raw_copy / "sales_pipeline.csv")
    pd.concat([pipeline, pipeline.head(1)]).to_csv(raw_copy / "sales_pipeline.csv", index=False)
    with pytest.raises(DataQualityError, match="chave primária"):
        run(raw_copy, out_dir=None)


def test_raw_files_are_preserved(raw_copy, tmp_path):
    before = _digest(raw_copy)
    run(raw_copy, tmp_path / "out")
    assert _digest(raw_copy) == before
    assert (tmp_path / "out" / "opportunities_analytic.csv").exists()
    assert (tmp_path / "out" / "data_quality_issues.csv").exists()


def test_cannot_write_over_raw_data(raw_copy):
    with pytest.raises(ValueError, match="brutos"):
        run(raw_copy, raw_copy)


def test_every_column_has_a_declared_role(result):
    assert list(result.analytic.columns) == list(COLUMN_ROLES)


def test_outcome_columns_are_empty_for_open_deals(result):
    df = result.analytic
    open_deals = df[df["is_open"]]
    for col in ["is_won", "close_date", "close_value", "cycle_days", "close_to_list_ratio"]:
        assert open_deals[col].isna().all(), col
    assert COLUMN_ROLES["close_value"] == OUTCOME


def test_missing_values_follow_policy(result):
    df = result.analytic
    assert not df.loc[~df["is_open"], "account_missing"].any()  # conta ausente só em abertos
    assert df.loc[df["deal_stage"] == "Prospecting", "engage_date"].isna().all()
    assert df.loc[df["deal_stage"] == "Prospecting", "age_days_at_reference"].isna().all()
    assert (df["is_subsidiary"].fillna(False) == df["subsidiary_of"].notna()).all()


def test_quality_issues_are_logged(result):
    checks = set(result.issues["check"])
    assert {"grafia inconsistente", "conta ausente", "possível deal duplicado",
            "truncamento à esquerda", "vendedor sem deals"} <= checks
    dup = result.issues.set_index("check").loc["possível deal duplicado", "rows"]
    assert dup == result.analytic["possible_duplicate"].sum() == 64


def test_app_loader_agrees_with_pipeline(result):
    """O loader do app e o pipeline aplicam as mesmas correções."""
    app = load_deals().set_index("opportunity_id").sort_index()
    pipe = result.analytic.set_index("opportunity_id").sort_index()
    for col in ["product", "sales_price", "manager", "regional_office", "deal_stage"]:
        assert (app[col] == pipe[col]).all(), col
    assert (app["sector"].fillna("-") == pipe["sector"].fillna("-")).all()
