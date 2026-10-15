"""Pipeline reprodutível: CSVs brutos do CRM -> tabela analítica consolidada + log de qualidade.

Garantias:
- Os arquivos originais só são lidos; as saídas vão para outro diretório.
- Chaves primárias e estrangeiras são validadas antes dos joins, e os joins usam
  `validate="many_to_one"` para impedir que uma linha seja duplicada silenciosamente.
- Cada valor ausente tem um tratamento explícito (MISSING_POLICY), e cada problema
  encontrado vira uma linha no log de qualidade.
- Toda coluna da tabela final tem um papel declarado (COLUMN_ROLES). As colunas de
  desfecho nunca devem ser usadas como preditoras.

Uso:
    python -m src.data_processing                # lê data/, escreve data/processed/
    python -m src.data_processing --out outra/pasta
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data"
OUT_DIR = RAW_DIR / "processed"

# Data de referência ("hoje") para a idade dos deals abertos: a última data do CRM.
REFERENCE_DATE = pd.Timestamp("2017-12-31")

EXPECTED_COLUMNS = {
    "accounts": ["account", "sector", "year_established", "revenue", "employees", "office_location", "subsidiary_of"],
    "products": ["product", "series", "sales_price"],
    "sales_teams": ["sales_agent", "manager", "regional_office"],
    "sales_pipeline": [
        "opportunity_id", "sales_agent", "product", "account",
        "deal_stage", "engage_date", "close_date", "close_value",
    ],
}
PRIMARY_KEYS = {
    "accounts": "account",
    "products": "product",
    "sales_teams": "sales_agent",
    "sales_pipeline": "opportunity_id",
}
STAGES = ("Prospecting", "Engaging", "Won", "Lost")
OPEN_STAGES = ("Prospecting", "Engaging")

# Correções de grafia: (tabela, coluna) -> {valor errado: valor correto}.
VALUE_FIXES = {
    ("sales_pipeline", "product"): {"GTXPro": "GTX Pro"},
    ("accounts", "sector"): {"technolgy": "technology"},
    ("accounts", "office_location"): {"Philipines": "Philippines"},
}

# Como cada ausência é tratada na tabela analítica.
MISSING_POLICY = {
    "account": "Mantido nulo; `account_missing` = True. Ocorre só em deals abertos.",
    "sector / revenue / employees / year_established / office_location":
        "Nulos quando não há conta (herdado do left join). Não são imputados.",
    "subsidiary_of": "Nulo significa empresa independente, não dado faltante; `is_subsidiary` = False.",
    "engage_date": "Nulo em todo Prospecting (o deal ainda não foi engajado). Não é imputado.",
    "close_date / close_value": "Nulos em todo deal aberto (ainda sem desfecho). Não são imputados.",
}

# Papel de cada coluna da tabela analítica.
ID, PRE, OUTCOME, AUX = "identificador", "pré-desfecho", "desfecho (não usar como preditor)", "auxiliar"
COLUMN_ROLES = {
    "opportunity_id": ID,
    "sales_agent": PRE, "manager": PRE, "regional_office": PRE,
    "product": PRE, "series": PRE, "sales_price": PRE,
    "account": PRE, "account_missing": AUX,
    "sector": PRE, "year_established": PRE, "account_age_years": PRE,
    "revenue": PRE, "revenue_band": PRE, "employees": PRE, "employees_band": PRE,
    "office_location": PRE, "subsidiary_of": PRE, "is_subsidiary": PRE,
    "engage_date": PRE, "engage_month": PRE,
    "age_days_at_reference": PRE,
    "possible_duplicate": AUX,
    "deal_stage": OUTCOME, "is_open": OUTCOME, "is_won": OUTCOME,
    "close_date": OUTCOME, "close_value": OUTCOME,
    "cycle_days": OUTCOME, "close_to_list_ratio": OUTCOME,
}


@dataclass
class Issue:
    check: str
    table: str
    column: str
    severity: str  # erro | aviso | info
    rows: int
    action: str
    detail: str = ""


class QualityLog:
    def __init__(self) -> None:
        self.issues: list[Issue] = []

    def add(self, *args, **kwargs) -> None:
        self.issues.append(Issue(*args, **kwargs))

    def errors(self) -> list[Issue]:
        return [i for i in self.issues if i.severity == "erro"]

    def to_frame(self) -> pd.DataFrame:
        return pd.DataFrame([asdict(i) for i in self.issues], columns=list(Issue.__dataclass_fields__))


class DataQualityError(ValueError):
    """Problema que impede uma tabela analítica confiável."""


# ---------------------------------------------------------------- leitura

def load_raw(raw_dir: Path = RAW_DIR) -> dict[str, pd.DataFrame]:
    """Lê os quatro CSVs como texto (chaves) e números. Falha se faltar arquivo ou coluna."""
    missing = [n for n in EXPECTED_COLUMNS if not (raw_dir / f"{n}.csv").exists()]
    if missing:
        raise FileNotFoundError(f"arquivos ausentes em {raw_dir}: {missing}. Nenhum dado é inventado.")
    tables = {}
    for name, columns in EXPECTED_COLUMNS.items():
        df = pd.read_csv(raw_dir / f"{name}.csv")
        absent = set(columns) - set(df.columns)
        if absent:
            raise DataQualityError(f"{name}.csv sem as colunas {sorted(absent)}")
        tables[name] = df[columns]
    return tables


def profile(tables: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Volume, tipos, nulos e duplicidades por coluna."""
    rows = []
    for name, df in tables.items():
        for col in df.columns:
            rows.append({
                "table": name, "column": col, "dtype": str(df[col].dtype), "rows": len(df),
                "nulls": int(df[col].isna().sum()), "distinct": int(df[col].nunique()),
                "duplicated_full_rows_in_table": int(df.duplicated().sum()),
            })
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- validação e limpeza

def check_primary_keys(tables: dict[str, pd.DataFrame], log: QualityLog) -> None:
    for name, key in PRIMARY_KEYS.items():
        col = tables[name][key]
        n_null, n_dup = int(col.isna().sum()), int(col.duplicated().sum())
        if n_null or n_dup:
            log.add("chave primária", name, key, "erro", n_null + n_dup, "pipeline interrompido",
                    f"{n_null} nulos, {n_dup} duplicados")


def standardize(tables: dict[str, pd.DataFrame], log: QualityLog) -> dict[str, pd.DataFrame]:
    """Remove espaços nas bordas e corrige grafias conhecidas. Retorna cópias."""
    out = {name: df.copy() for name, df in tables.items()}
    for name, df in out.items():
        for col in df.columns:
            if pd.api.types.is_string_dtype(df[col]) or df[col].dtype == object:
                stripped = df[col].str.strip()
                present = df[col].notna()
                changed = int((stripped[present] != df.loc[present, col]).sum())
                if changed:
                    log.add("espaços nas bordas", name, col, "aviso", changed, "removidos")
                df[col] = stripped
    for (name, col), mapping in VALUE_FIXES.items():
        for wrong, right in mapping.items():
            n = int((out[name][col] == wrong).sum())
            if n:
                out[name][col] = out[name][col].replace({wrong: right})
                log.add("grafia inconsistente", name, col, "aviso", n, f"'{wrong}' -> '{right}'")
    pipeline = out["sales_pipeline"]
    pipeline["engage_date"] = pd.to_datetime(pipeline["engage_date"], errors="raise")
    pipeline["close_date"] = pd.to_datetime(pipeline["close_date"], errors="raise")
    return out


def check_foreign_keys(tables: dict[str, pd.DataFrame], log: QualityLog) -> None:
    pipeline, accounts = tables["sales_pipeline"], tables["accounts"]
    relations = [
        ("sales_pipeline", "product", pipeline["product"], tables["products"]["product"]),
        ("sales_pipeline", "sales_agent", pipeline["sales_agent"], tables["sales_teams"]["sales_agent"]),
        ("sales_pipeline", "account", pipeline["account"].dropna(), accounts["account"]),
        ("accounts", "subsidiary_of", accounts["subsidiary_of"].dropna(), accounts["account"]),
    ]
    for table, col, child, parent in relations:
        orphans = child[~child.isin(set(parent))]
        if len(orphans):
            log.add("chave estrangeira órfã", table, col, "erro", len(orphans), "pipeline interrompido",
                    f"valores sem correspondência: {sorted(orphans.unique())[:5]}")
    unused = set(tables["sales_teams"]["sales_agent"]) - set(pipeline["sales_agent"])
    if unused:
        log.add("vendedor sem deals", "sales_teams", "sales_agent", "info", len(unused),
                "mantidos na dimensão; não aparecem na tabela analítica", ", ".join(sorted(unused)))


def check_business_rules(pipeline: pd.DataFrame, log: QualityLog) -> None:
    """Regras de coerência entre estágio, datas e valores."""
    stage = pipeline["deal_stage"]
    is_open = stage.isin(OPEN_STAGES)
    unknown = ~stage.isin(STAGES)
    rules = [
        ("estágio desconhecido", "deal_stage", unknown, "erro"),
        ("Won com close_value <= 0", "close_value", stage.eq("Won") & ~(pipeline["close_value"] > 0), "erro"),
        ("Lost com close_value != 0", "close_value", stage.eq("Lost") & pipeline["close_value"].ne(0), "erro"),
        ("deal aberto com dado de fechamento", "close_date",
         is_open & (pipeline["close_date"].notna() | pipeline["close_value"].notna()), "erro"),
        ("deal fechado sem data ou valor", "close_date",
         ~is_open & (pipeline["close_date"].isna() | pipeline["close_value"].isna()), "erro"),
        ("close_date anterior a engage_date", "close_date", pipeline["close_date"] < pipeline["engage_date"], "erro"),
        ("Engaging/fechado sem engage_date", "engage_date",
         stage.ne("Prospecting") & pipeline["engage_date"].isna(), "erro"),
        ("Prospecting com engage_date", "engage_date", stage.eq("Prospecting") & pipeline["engage_date"].notna(), "erro"),
    ]
    for check, col, mask, severity in rules:
        n = int(mask.sum())
        if n:
            log.add(check, "sales_pipeline", col, severity, n, "pipeline interrompido")

    missing_account = pipeline["account"].isna()
    n_open_missing = int((missing_account & is_open).sum())
    n_closed_missing = int((missing_account & ~is_open).sum())
    log.add("conta ausente", "sales_pipeline", "account", "aviso", int(missing_account.sum()),
            "mantido nulo + flag account_missing",
            f"{n_open_missing} em deals abertos, {n_closed_missing} em fechados: a ausência depende do desfecho "
            "(risco de vazamento se usada como preditor)")
    log.add("Prospecting sem engage_date", "sales_pipeline", "engage_date", "info",
            int(stage.eq("Prospecting").sum()), "mantido nulo; idade não calculável", "esperado pelo processo")

    dup_key = ["sales_agent", "product", "account", "engage_date"]
    dups = pipeline["account"].notna() & pipeline.duplicated(dup_key, keep=False)
    if dups.any():
        log.add("possível deal duplicado", "sales_pipeline", "+".join(dup_key), "aviso", int(dups.sum()),
                "mantidos + flag possible_duplicate",
                "mesmo vendedor, produto, conta e data de engajamento; IDs diferentes")

    first_close = pipeline["close_date"].min()
    early = int((pipeline["engage_date"] < first_close).sum())
    log.add("truncamento à esquerda", "sales_pipeline", "close_date", "aviso", early,
            "documentado; não usar mês de engajamento como preditor",
            f"nenhum fechamento antes de {first_close:%Y-%m-%d}, mas há engajamentos desde "
            f"{pipeline['engage_date'].min():%Y-%m-%d}: deals antigos que fecharam cedo não estão no dataset")


# ---------------------------------------------------------------- tabela analítica

def _quartile_band(values: pd.Series, labels: list[str]) -> pd.Series:
    return pd.qcut(values, 4, labels=labels)


def build_analytic_table(tables: dict[str, pd.DataFrame], reference_date: pd.Timestamp = REFERENCE_DATE) -> pd.DataFrame:
    accounts = tables["accounts"].copy()
    # Faixas de porte calculadas sobre as contas (não sobre deals), para não ponderar por volume.
    accounts["revenue_band"] = _quartile_band(accounts["revenue"], ["Q1 (menor)", "Q2", "Q3", "Q4 (maior)"])
    accounts["employees_band"] = _quartile_band(accounts["employees"], ["Q1 (menor)", "Q2", "Q3", "Q4 (maior)"])
    accounts["is_subsidiary"] = accounts["subsidiary_of"].notna()
    accounts["account_age_years"] = reference_date.year - accounts["year_established"]

    pipeline = tables["sales_pipeline"]
    df = (
        pipeline.merge(tables["sales_teams"], on="sales_agent", how="left", validate="many_to_one")
        .merge(tables["products"], on="product", how="left", validate="many_to_one")
        .merge(accounts, on="account", how="left", validate="many_to_one")
    )
    if len(df) != len(pipeline):
        raise DataQualityError(f"join alterou o número de linhas: {len(pipeline)} -> {len(df)}")

    df["account_missing"] = df["account"].isna()
    df["is_subsidiary"] = df["is_subsidiary"].astype("boolean")  # nulo quando não há conta
    df["is_open"] = df["deal_stage"].isin(OPEN_STAGES)
    # Desfecho: True/False só para fechados; nulo (pd.NA) para abertos.
    df["is_won"] = df["deal_stage"].map({"Won": True, "Lost": False}).astype("boolean")
    df["engage_month"] = df["engage_date"].dt.to_period("M").astype(str).replace("NaT", pd.NA)
    df["age_days_at_reference"] = (reference_date - df["engage_date"]).dt.days.where(df["deal_stage"].eq("Engaging"))
    df["cycle_days"] = (df["close_date"] - df["engage_date"]).dt.days
    df["close_to_list_ratio"] = (df["close_value"] / df["sales_price"]).where(df["deal_stage"].eq("Won"))

    dup_key = ["sales_agent", "product", "account", "engage_date"]
    df["possible_duplicate"] = df["account"].notna() & df.duplicated(dup_key, keep=False)
    return df[list(COLUMN_ROLES)]


def reconcile(raw: dict[str, pd.DataFrame], analytic: pd.DataFrame, log: QualityLog) -> pd.DataFrame:
    """Confere que nada foi perdido ou duplicado entre o bruto e a tabela final."""
    src = raw["sales_pipeline"]
    checks = [
        ("linhas", len(src), len(analytic)),
        ("opportunity_id distintos", src["opportunity_id"].nunique(), analytic["opportunity_id"].nunique()),
        ("soma de close_value", float(src["close_value"].sum()), float(analytic["close_value"].sum())),
    ] + [
        (f"deals {s}", int((src["deal_stage"] == s).sum()), int((analytic["deal_stage"] == s).sum())) for s in STAGES
    ]
    result = pd.DataFrame(checks, columns=["check", "raw", "analytic"])
    result["ok"] = result["raw"] == result["analytic"]
    for row in result[~result["ok"]].itertuples():
        log.add("reconciliação", "analytic", row.check, "erro", 0, "pipeline interrompido",
                f"bruto={row.raw} analítico={row.analytic}")
    return result


@dataclass
class PipelineResult:
    analytic: pd.DataFrame
    issues: pd.DataFrame
    profile: pd.DataFrame
    reconciliation: pd.DataFrame


def run(raw_dir: Path = RAW_DIR, out_dir: Path | None = OUT_DIR,
        reference_date: pd.Timestamp = REFERENCE_DATE) -> PipelineResult:
    """Executa o pipeline. Com `out_dir=None`, não grava nada (uso em testes e análises)."""
    log = QualityLog()
    raw = load_raw(raw_dir)
    table_profile = profile(raw)

    check_primary_keys(raw, log)
    clean = standardize(raw, log)
    check_foreign_keys(clean, log)
    check_business_rules(clean["sales_pipeline"], log)
    if log.errors():
        raise DataQualityError("; ".join(f"{i.check} ({i.table}.{i.column}): {i.detail}" for i in log.errors()))

    analytic = build_analytic_table(clean, reference_date)
    reconciliation = reconcile(raw, analytic, log)
    if log.errors():
        raise DataQualityError("reconciliação falhou: " + "; ".join(i.detail for i in log.errors()))

    result = PipelineResult(analytic, log.to_frame(), table_profile, reconciliation)
    if out_dir is not None:
        out_dir = Path(out_dir)
        if out_dir.resolve() == Path(raw_dir).resolve():
            raise ValueError("out_dir não pode ser o diretório dos dados brutos")
        out_dir.mkdir(parents=True, exist_ok=True)
        result.analytic.to_csv(out_dir / "opportunities_analytic.csv", index=False)
        result.issues.to_csv(out_dir / "data_quality_issues.csv", index=False)
        result.profile.to_csv(out_dir / "table_profile.csv", index=False)
        result.reconciliation.to_csv(out_dir / "reconciliation.csv", index=False)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--raw", type=Path, default=RAW_DIR)
    parser.add_argument("--out", type=Path, default=OUT_DIR)
    args = parser.parse_args()
    result = run(args.raw, args.out)
    pd.set_option("display.width", 200, "display.max_colwidth", 120)
    print(f"Tabela analítica: {result.analytic.shape[0]} linhas x {result.analytic.shape[1]} colunas -> {args.out}")
    print("\nReconciliação:\n" + result.reconciliation.to_string(index=False))
    print("\nProblemas de qualidade:\n" + result.issues.to_string(index=False))


if __name__ == "__main__":
    main()
