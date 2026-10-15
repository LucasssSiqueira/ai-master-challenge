import pandas as pd
import pytest

from lead_scorer.data_loader import DataValidationError, build_deals, load_deals, load_raw


@pytest.fixture(scope="module")
def deals():
    return load_deals()


def test_all_rows_preserved(deals):
    assert len(deals) == 8800


def test_every_deal_has_a_price(deals):
    # Sem a correção GTXPro -> GTX Pro, 1.480 deals ficariam sem preço.
    assert deals["sales_price"].notna().all()
    assert "GTXPro" not in set(deals["product"])


def test_open_pipeline_size(deals):
    assert deals["is_open"].sum() == 2089
    assert (~deals.loc[deals["is_open"], "has_account"]).sum() == 1425


def test_sector_typo_fixed(deals):
    assert "technolgy" not in set(deals["sector"].dropna())


def test_unknown_product_fails_loudly():
    raw = load_raw()
    raw["pipeline"] = raw["pipeline"].copy()
    raw["pipeline"].loc[0, "product"] = "Produto Fantasma"
    with pytest.raises(DataValidationError, match="sem preço"):
        build_deals(raw)


def test_dates_parsed(deals):
    assert pd.api.types.is_datetime64_any_dtype(deals["engage_date"])
