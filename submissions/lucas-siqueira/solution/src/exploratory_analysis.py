"""Análise exploratória sobre a tabela analítica. Gera todos os números de docs/04-data-analysis.md.

Uso: python -m src.exploratory_analysis
"""
from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .data_processing import COLUMN_ROLES, OUTCOME, run

HOLDOUT_CUTOFF = pd.Timestamp("2017-09-30")  # treino: fechados até aqui; teste: fechados depois
K_SHRINKAGE = 50
N_PERMUTATIONS = 2000
SNAPSHOTS = pd.date_range("2017-03-31", "2017-11-30", freq="ME")


def wilson(wins: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """Intervalo de confiança de 95% para uma proporção."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = wins / n
    center = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return center - half, center + half


def auc(y: pd.Series, score: pd.Series) -> float:
    """Probabilidade de um positivo ter score maior que um negativo (0,5 = acaso)."""
    y = y.astype(bool).to_numpy()
    ranks = pd.Series(score).rank().to_numpy()
    n1, n0 = y.sum(), (~y).sum()
    return float((ranks[y].sum() - n1 * (n1 + 1) / 2) / (n1 * n0))


def chi2_stat(codes: np.ndarray, y: np.ndarray, k: int) -> float:
    n_cat = np.bincount(codes, minlength=k)
    wins = np.bincount(codes, weights=y, minlength=k)
    p = y.mean()
    expected_w, expected_l = n_cat * p, n_cat * (1 - p)
    mask = n_cat > 0
    return float((((wins - expected_w) ** 2 / expected_w)[mask] + (((n_cat - wins) - expected_l) ** 2 / expected_l)[mask]).sum())


def association(closed: pd.DataFrame, column: str, seed: int = 0) -> dict:
    """Qui-quadrado com p-valor por permutação e V de Cramér (força da associação, 0 a 1)."""
    data = closed[[column, "is_won"]].dropna()
    codes, _ = pd.factorize(data[column].astype(str))
    y = data["is_won"].astype(float).to_numpy()
    k = codes.max() + 1
    observed = chi2_stat(codes, y, k)
    rng = np.random.default_rng(seed)
    perm = np.array([chi2_stat(codes, rng.permutation(y), k) for _ in range(N_PERMUTATIONS)])
    p_value = (np.sum(perm >= observed) + 1) / (N_PERMUTATIONS + 1)
    cramers_v = math.sqrt(observed / len(data)) if k > 1 else 0.0
    return {"variável": column, "categorias": k, "n": len(data), "qui2": round(observed, 1),
            "p_permutação": round(p_value, 4), "V_de_Cramér": round(cramers_v, 3)}


def conversion_table(closed: pd.DataFrame, column: str) -> pd.DataFrame:
    g = closed.groupby(column, observed=True)["is_won"].agg(ganhos="sum", fechados="count")
    g["win_rate"] = g["ganhos"] / g["fechados"]
    ci = [wilson(int(w), int(n)) for w, n in zip(g["ganhos"], g["fechados"])]
    g["ic95_inf"], g["ic95_sup"] = zip(*ci)
    return g.sort_values("win_rate").round(3)


def holdout_auc(closed: pd.DataFrame) -> pd.DataFrame:
    """AUC em teste temporal de cada variável pré-desfecho candidata."""
    train = closed[closed["close_date"] <= HOLDOUT_CUTOFF]
    test = closed[closed["close_date"] > HOLDOUT_CUTOFF]
    base = train["is_won"].mean()
    rows = []
    for col in ["sales_agent", "manager", "regional_office", "product", "series", "account", "sector",
                "office_location", "revenue_band", "employees_band", "is_subsidiary"]:
        g = train.groupby(col, observed=True)["is_won"].agg(["sum", "count"])
        rate = (g["sum"] + K_SHRINKAGE * base) / (g["count"] + K_SHRINKAGE)
        score = test[col].astype(object).map(rate.to_dict()).astype(float).fillna(base)
        rows.append({"variável": col, "tipo": "categórica (win rate histórico com shrinkage)",
                     "AUC_teste": round(auc(test["is_won"], score), 3)})
    for col in ["sales_price", "revenue", "employees", "account_age_years"]:
        rows.append({"variável": col, "tipo": "numérica (valor bruto)",
                     "AUC_teste": round(auc(test["is_won"], test[col]), 3)})
    return pd.DataFrame(rows), len(train), len(test)


def snapshot_age_auc(df: pd.DataFrame) -> pd.DataFrame:
    """Idade do deal em datas passadas, usando só deals que estavam abertos naquele dia."""
    closed = df[df["is_won"].notna()]
    rows = []
    for snap in SNAPSHOTS:
        open_then = closed[(closed["engage_date"] <= snap) & (closed["close_date"] > snap)]
        age = (snap - open_then["engage_date"]).dt.days
        rows.append({"snapshot": snap.date(), "deals_abertos": len(open_then),
                     "win_rate": round(open_then["is_won"].mean(), 3),
                     "AUC_idade": round(auc(open_then["is_won"], age), 3)})
    return pd.DataFrame(rows)


def main() -> None:
    pd.set_option("display.width", 200, "display.max_rows", 100)
    df = run(out_dir=None).analytic
    closed = df[df["is_won"].notna()].copy()
    closed["is_won"] = closed["is_won"].astype(bool)
    section = lambda title: print(f"\n{'=' * 8} {title} {'=' * 8}")

    section("Distribuição de estágios")
    stages = df["deal_stage"].value_counts()
    print(pd.DataFrame({"deals": stages, "%": (stages / len(df) * 100).round(1)}))
    print(f"win rate global (Won / fechados) = {closed['is_won'].mean():.4f}  (n fechados = {len(closed)})")

    section("Conversão por variável (fechados)")
    for col in ["product", "sector", "regional_office", "manager", "revenue_band", "employees_band", "is_subsidiary"]:
        print(f"\n-- {col}\n{conversion_table(closed, col)}")
    agents = conversion_table(closed, "sales_agent")
    print(f"\n-- sales_agent (n={len(agents)}): win rate de {agents['win_rate'].min():.3f} a {agents['win_rate'].max():.3f}, "
          f"desvio-padrão {agents['win_rate'].std():.3f}")
    print(agents.head(3)); print("..."); print(agents.tail(3))
    expected_sd = math.sqrt(closed['is_won'].mean() * (1 - closed['is_won'].mean()) / agents['fechados'].median())
    print(f"desvio-padrão esperado só por acaso com n mediano={agents['fechados'].median():.0f}: {expected_sd:.3f}")
    overlap = (agents["ic95_inf"] <= closed["is_won"].mean()) & (agents["ic95_sup"] >= closed["is_won"].mean())
    print(f"vendedores cujo IC95% contém a média global: {overlap.sum()} de {len(agents)}")

    section("Teste de associação (qui-quadrado por permutação)")
    print(pd.DataFrame([association(closed, c) for c in
                        ["product", "sector", "regional_office", "manager", "sales_agent",
                         "revenue_band", "employees_band", "is_subsidiary", "office_location"]]).to_string(index=False))

    section("Holdout temporal (AUC)")
    table, n_train, n_test = holdout_auc(closed)
    print(f"treino: fechados até {HOLDOUT_CUTOFF.date()} (n={n_train}); teste: depois (n={n_test})")
    print(table.to_string(index=False))

    section("Tempo no pipeline")
    print(closed.groupby("deal_stage")["cycle_days"].describe().round(1))
    won_cycle = closed.loc[closed["is_won"], "cycle_days"]
    print("Won p25/p50/p75/p95/max:", [float(won_cycle.quantile(q)) for q in (.25, .5, .75, .95)], won_cycle.max())
    print("Lost mediana:", closed.loc[~closed["is_won"], "cycle_days"].median(),
          "| Lost em até 14 dias: %.3f" % (closed.loc[~closed["is_won"], "cycle_days"] <= 14).mean())
    engaging = df[df["deal_stage"] == "Engaging"]["age_days_at_reference"]
    print("Engaging abertos: idade em 31/12/2017", engaging.describe().round(1).to_dict())
    print(f"Engaging com idade > 138 dias: {(engaging > 138).sum()} ({(engaging > 138).mean():.3f})")
    bins = [-1, 7, 14, 30, 60, 90, 120, 138]
    by_cycle = closed.assign(faixa=pd.cut(closed["cycle_days"], bins)).groupby("faixa", observed=True)["is_won"].agg(["mean", "count"])
    print("win rate por ciclo TOTAL (desfecho, vazamento):\n", by_cycle.round(3))
    print("P(win | deal ainda aberto após a dias):")
    for a in [0, 7, 14, 30, 60, 90, 120]:
        s = closed[closed["cycle_days"] > a]
        print(f"  a>{a:>3}: {s['is_won'].mean():.3f} (n={len(s)})")
    print("\nIdade em snapshots passados (sem vazamento):\n", snapshot_age_auc(df).to_string(index=False))

    section("Vazamento")
    print(f"AUC de cycle_days (fechados): {auc(closed['is_won'], closed['cycle_days']):.3f}  <- conhecido só no fechamento")
    print(f"AUC de close_value (fechados): {auc(closed['is_won'], closed['close_value']):.3f}  <- Lost = 0 por definição")
    print(f"account_missing entre fechados: {closed['account_missing'].sum()} | entre abertos: {df.loc[df['is_open'], 'account_missing'].sum()} de {df['is_open'].sum()}")
    print("colunas de desfecho:", [c for c, r in COLUMN_ROLES.items() if r == OUTCOME])

    section("Viés de seleção: por mês de engajamento")
    m = df[df["engage_date"].notna()].groupby("engage_month").agg(
        deals=("opportunity_id", "size"),
        pct_fechados=("is_open", lambda s: 1 - s.mean()),
        win_rate=("is_won", lambda s: s.dropna().astype(bool).mean()),
        ciclo_mediano=("cycle_days", "median"),
    )
    print(m.round(3).to_string())
    print(f"primeiro fechamento: {df['close_date'].min().date()} | primeiro engajamento: {df['engage_date'].min().date()}")

    section("Valor")
    won = closed[closed["is_won"]]
    print("close_value / preço de lista (Won):", won["close_to_list_ratio"].describe().round(3).to_dict())
    print("preços:", df.drop_duplicates("product").set_index("product")["sales_price"].sort_values().to_dict())
    print("open por produto:\n", df[df["is_open"]].groupby(["product", "deal_stage"]).size().unstack(fill_value=0))


if __name__ == "__main__":
    main()
