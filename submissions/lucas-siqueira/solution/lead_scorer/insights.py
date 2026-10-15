"""O que o vendedor precisa saber hoje: a frase do topo, as prioridades e um insight acionável.

Funções puras sobre a lista já pontuada (saída de `build_priority_list`), para que a tela
principal não faça contas e tudo possa ser testado.
"""
from dataclasses import dataclass

import pandas as pd

from .explain import money_short
from .scoring import BAND_ORDER

ACTIVE_BANDS = ["Alta", "Média", "Baixa"]


@dataclass(frozen=True)
class Insight:
    metric: str       # número grande
    label: str        # o que o número significa
    detail: str       # uma frase de contexto
    action: str       # o que fazer
    page: str         # onde agir: "requalify" | "pipeline"
    cta: str          # texto do botão


def priorities(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """Os n deals mais relevantes. A lista já vem ordenada por faixa e score; parados ficam de fora."""
    return df[df["band"] != "Requalificar"].head(n)


def headline(df: pd.DataFrame) -> str:
    top = priorities(df)
    if top.empty:
        return "Nenhum deal ativo hoje. Comece confirmando os deals parados."
    noun = "deal que precisa" if len(top) == 1 else "deals que precisam"
    return f"O Lead Scorer encontrou {money_short(top['sales_price'].sum())} em {len(top)} {noun} de você hoje."


def main_insight(df: pd.DataFrame, stale_days: int) -> Insight:
    """O insight de maior impacto para o recorte atual, em ordem de urgência."""
    total_value = df["sales_price"].sum()
    stale = df[df["band"] == "Requalificar"]
    stale_share = stale["sales_price"].sum() / total_value if total_value else 0.0
    if len(stale) and stale_share >= 0.5:
        n_first = min(5, len(stale))
        return Insight(
            metric=f"{stale_share:.0%}",
            label="do valor em aberto está parado",
            detail=(f"{len(stale)} deals ({money_short(stale['sales_price'].sum())}) estão há mais de "
                    f"{stale_days} dias em negociação. Nenhum deal do histórico fechou depois disso."),
            action=f"Confirme ou encerre os {n_first} de maior valor esta semana.",
            page="requalify",
            cta="Revisar deals parados",
        )

    slipping = df[df["band"].isin(["Alta", "Média"]) & df["timing_segment"].isin(["late", "very_late"])]
    if len(slipping):
        return Insight(
            metric=str(len(slipping)),
            label="deals importantes saindo da janela",
            detail=f"Somam {money_short(slipping['sales_price'].sum())} e já passaram do prazo em que ganhos costumam fechar.",
            action="Combine uma data de decisão com cada cliente.",
            page="pipeline",
            cta="Ver no pipeline",
        )

    missing = df["account"].isna()
    if len(df) and missing.mean() >= 0.5:
        return Insight(
            metric=f"{missing.mean():.0%}",
            label="dos deals sem conta no CRM",
            detail="Sem a conta, não há setor nem porte do cliente para orientar a abordagem.",
            action="Preencha a conta nos deals de maior valor.",
            page="pipeline",
            cta="Ver no pipeline",
        )

    qualify = df[df["band"] == "Qualificar"]
    return Insight(
        metric=str(len(qualify)),
        label="deals aguardando qualificação",
        detail=f"Somam {money_short(qualify['sales_price'].sum())} em preço de lista.",
        action="Marque a primeira reunião com os de maior valor.",
        page="pipeline",
        cta="Ver no pipeline",
    )


def band_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Contagem, valor e participação por faixa, sempre com as 5 faixas na mesma ordem."""
    grouped = df.groupby("band", observed=False).agg(deals=("opportunity_id", "count"), value=("sales_price", "sum"))
    grouped = grouped.reindex(BAND_ORDER, fill_value=0)
    total = grouped["deals"].sum()
    grouped["share"] = grouped["deals"] / total if total else 0.0
    return grouped


def active_share(df: pd.DataFrame) -> float:
    """Fração dos deals abertos que não está parada."""
    return float((df["band"] != "Requalificar").mean()) if len(df) else 0.0
