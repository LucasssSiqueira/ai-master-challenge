"""Leitura, limpeza e junção das quatro tabelas do CRM."""
from pathlib import Path

import pandas as pd

from .config import DATA_DIR, OPEN_STAGES, PRODUCT_FIXES, SECTOR_FIXES, STAGES


# Mesmo vendedor, produto, conta e data de engajamento com IDs diferentes: possível duplicata.
DUPLICATE_KEY = ["sales_agent", "product", "account", "engage_date"]


class DataValidationError(ValueError):
    """Os dados não respeitam uma premissa da qual o scoring depende."""


def load_raw(data_dir: Path = DATA_DIR) -> dict[str, pd.DataFrame]:
    return {
        "pipeline": pd.read_csv(data_dir / "sales_pipeline.csv", parse_dates=["engage_date", "close_date"]),
        "accounts": pd.read_csv(data_dir / "accounts.csv"),
        "products": pd.read_csv(data_dir / "products.csv"),
        "teams": pd.read_csv(data_dir / "sales_teams.csv"),
    }


def build_deals(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Uma linha por oportunidade, já com vendedor, produto e conta anexados."""
    pipeline = raw["pipeline"].copy()
    pipeline["product"] = pipeline["product"].replace(PRODUCT_FIXES)

    accounts = raw["accounts"].copy()
    accounts["sector"] = accounts["sector"].replace(SECTOR_FIXES)

    # Left joins: 68% dos deals abertos não têm conta e não podem sumir.
    deals = (
        pipeline.merge(raw["teams"], on="sales_agent", how="left")
        .merge(raw["products"], on="product", how="left")
        .merge(accounts, on="account", how="left")
    )
    _validate(deals, expected_rows=len(pipeline))

    deals["is_open"] = deals["deal_stage"].isin(OPEN_STAGES)
    deals["is_won"] = deals["deal_stage"].eq("Won")
    deals["has_account"] = deals["account"].notna()
    deals["cycle_days"] = (deals["close_date"] - deals["engage_date"]).dt.days
    deals["possible_duplicate"] = deals["has_account"] & deals.duplicated(DUPLICATE_KEY, keep=False)
    return deals


def _validate(deals: pd.DataFrame, expected_rows: int) -> None:
    problems = []
    if len(deals) != expected_rows:
        problems.append(f"join alterou o número de linhas ({expected_rows} -> {len(deals)})")
    if deals["sales_price"].isna().any():
        missing = sorted(deals.loc[deals["sales_price"].isna(), "product"].unique())
        problems.append(f"produtos sem preço no catálogo: {missing}")
    if deals["manager"].isna().any():
        problems.append("deals com vendedor fora de sales_teams")
    unknown = set(deals["deal_stage"]) - STAGES
    if unknown:
        problems.append(f"deal_stage desconhecido: {unknown}")
    if problems:
        raise DataValidationError("; ".join(problems))


def load_deals(data_dir: Path = DATA_DIR) -> pd.DataFrame:
    return build_deals(load_raw(data_dir))
