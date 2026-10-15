"""Lead Scorer — interface do vendedor. Só apresentação: regras de negócio ficam em lead_scorer/."""
import pandas as pd
import streamlit as st

from lead_scorer.backtest import run_backtest
from lead_scorer.config import DEFAULT_CONFIG as CFG
from lead_scorer.data_loader import load_deals
from lead_scorer.explain import money
from lead_scorer.scoring import BAND_ORDER, build_priority_list

BAND_LABEL = {
    "Alta": "🟢 Alta",
    "Média": "🟡 Média",
    "Baixa": "⚪ Baixa",
    "Qualificar": "🔵 Qualificar",
    "Requalificar": "🔴 Requalificar",
}
VIEW_COLUMN = {"Vendedor": "sales_agent", "Manager": "manager", "Região": "regional_office"}

st.set_page_config(page_title="Lead Scorer", page_icon="🎯", layout="wide")


@st.cache_data
def load():
    deals = load_deals()
    pipeline, stats = build_priority_list(deals)
    pipeline["band"] = pipeline["band"].astype(str)
    return deals, pipeline, stats


@st.cache_data
def backtest():
    return run_backtest(load_deals())


deals, pipeline, stats = load()

# ---------- Filtros ----------
with st.sidebar:
    st.header("🎯 Lead Scorer")
    view = st.radio("Ver pipeline por", ["Vendedor", "Manager", "Região", "Time todo"])
    if view == "Time todo":
        selected = None
        df = pipeline
    else:
        column = VIEW_COLUMN[view]
        options = sorted(pipeline[column].unique())
        selected = st.selectbox(view, options)
        df = pipeline[pipeline[column] == selected]
    st.caption(f"Pipeline em **{CFG.reference_date:%d/%m/%Y}** (última data do CRM).")
    st.caption(
        f"O score (0–100) soma **Valor** (até {CFG.weight_value:.0f}) e **Momento** (até {CFG.weight_timing:.0f}). "
        "A chance histórica aparece como informação. Veja a aba *Como o score funciona*."
    )

def money_short(value: float) -> str:
    """Valor compacto para os KPIs, que truncam em telas estreitas."""
    if value >= 1_000_000:
        return f"US$ {value / 1_000_000:.1f} mi".replace(".", ",")
    if value >= 1_000:
        return f"US$ {value / 1_000:.0f} mil"
    return money(value)


title = "Time todo" if selected is None else selected
st.title(f"Pipeline — {title}")

active = df[df["band"] != "Requalificar"]
stale = df[df["band"] == "Requalificar"]
k1, k2, k3, k4 = st.columns(4)
k1.metric("Deals abertos", len(df))
k2.metric("Prioridade Alta", int((df["band"] == "Alta").sum()))
k3.metric("Valor em deals ativos", money_short(active["sales_price"].sum()))
k4.metric(f"Valor parado ({len(stale)} deals)", money_short(stale["sales_price"].sum()))


def band_label(band: str) -> str:
    return BAND_LABEL[band]


def deal_title(row: pd.Series) -> str:
    account = row["account"] if isinstance(row["account"], str) else "Conta não informada"
    return f"{row['product']} · {account} · {money(row['sales_price'])}"


def score_breakdown(row: pd.Series) -> None:
    for label, col, weight in [
        ("Valor", "score_value", CFG.weight_value),
        ("Momento", "score_timing", CFG.weight_timing),
        ("Chance", "score_prob", CFG.weight_prob),
    ]:
        if weight == 0:
            continue
        pts = row[col]
        st.progress(min(pts / weight, 1.0), text=f"{label}: {pts:.0f} de {weight:.0f} pontos")


# ---------- Foco da semana ----------
st.subheader("Seu foco esta semana")
focus = active.head(5)
if focus.empty:
    st.info("Nenhum deal ativo. Comece pela aba **Requalificar**: confirme o que ainda está vivo.")
for rank, (_, row) in enumerate(focus.iterrows(), start=1):
    with st.container(border=True):
        left, right = st.columns([1, 4])
        left.metric(f"#{rank} · {band_label(row['band'])}", row["score"])
        right.markdown(f"**{deal_title(row)}**  \n👉 {row['action']}")
        right.caption("  \n".join(row["reasons"]))
        if selected is None or view != "Vendedor":
            right.caption(f"Vendedor: {row['sales_agent']}")


def deals_table(data: pd.DataFrame, key: str) -> pd.Series | None:
    """Tabela com seleção de linha; devolve o deal selecionado."""
    show = pd.DataFrame({
        "Faixa": data["band"].map(BAND_LABEL),
        "Score": data["score"],
        "Produto": data["product"],
        "Valor": data["sales_price"],
        "Conta": data["account"].fillna("— não informada"),
        "Dias engajado": data["age_days"],
        "Vendedor": data["sales_agent"],
        "Próxima ação": data["action"],
        "ID": data["opportunity_id"],
    })
    event = st.dataframe(
        show,
        hide_index=True,
        width="stretch",
        on_select="rerun",
        selection_mode="single-row",
        key=key,
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "Valor": st.column_config.NumberColumn("Valor (US$)", format="%d"),
            "Dias engajado": st.column_config.NumberColumn(format="%d"),
            "Próxima ação": st.column_config.TextColumn(width="large"),
        },
    )
    rows = event.selection.rows
    return data.iloc[rows[0]] if rows else None


def deal_detail(row: pd.Series | None) -> None:
    if row is None:
        st.caption("Clique em uma linha para ver por que o deal tem esse score.")
        return
    with st.container(border=True):
        st.markdown(f"#### {deal_title(row)} — score {row['score']} ({band_label(row['band'])})")
        c1, c2 = st.columns([2, 3])
        with c1:
            score_breakdown(row)
        with c2:
            st.markdown(f"**👉 {row['action']}**")
            for reason in row["reasons"]:
                st.markdown(f"- {reason}")
        st.caption(
            f"ID {row['opportunity_id']} · {row['sales_agent']} · {row['manager']} · região {row['regional_office']}"
        )


tab_all, tab_stale, tab_how = st.tabs(
    ["📋 Deals ativos", f"🔴 Requalificar ({len(stale)})", "ℹ️ Como o score funciona"]
)

with tab_all:
    bands = st.multiselect(
        "Faixas", [b for b in BAND_ORDER if b != "Requalificar"],
        default=[b for b in BAND_ORDER if b != "Requalificar"],
        format_func=band_label,
    )
    deal_detail(deals_table(active[active["band"].isin(bands)], key="active"))

    if view != "Vendedor":
        st.subheader("Resumo por vendedor")
        summary = (
            df.assign(
                alta=df["band"].eq("Alta"),
                parado=df["band"].eq("Requalificar"),
                valor_parado=df["sales_price"].where(df["band"].eq("Requalificar"), 0),
            )
            .groupby("sales_agent")
            .agg(abertos=("opportunity_id", "count"), alta=("alta", "sum"),
                 parados=("parado", "sum"), valor_parado=("valor_parado", "sum"))
            .sort_values("valor_parado", ascending=False)
            .reset_index()
        )
        summary.columns = ["Vendedor", "Abertos", "Prioridade Alta", "Parados", "Valor parado (US$)"]
        st.dataframe(summary, hide_index=True, width="stretch")

with tab_stale:
    st.markdown(
        f"Estes deals estão em *Engaging* há mais de **{CFG.stale_days} dias**, mais do que qualquer "
        "deal já fechado no histórico. Provavelmente estão mortos e só ocupam espaço no pipeline. "
        "Comece pelos de maior valor: confirme com o cliente ou encerre."
    )
    deal_detail(deals_table(stale.sort_values("sales_price", ascending=False), key="stale"))

with tab_how:
    st.markdown(
        f"""
### O que o score mede

| Componente | Pontos | O que significa |
|---|---|---|
| **Valor** | até {CFG.weight_value:.0f} | Preço do produto em escala logarítmica. O GTK 500 custa ~490× o MG Special; sem o log, o score seria só "ordenar por valor". |
| **Momento** | até {CFG.weight_timing:.0f} | Máximo quando o deal está na janela em que os deals ganhos costumam fechar ({stats.won_p25:.0f}–{stats.won_p75:.0f} dias de engajamento). Cai depois disso e zera aos {CFG.stale_days} dias. |
| **Chance** | {CFG.weight_prob:.0f} (informativo) | Taxa de vitória do vendedor com aquele produto, puxada para a média do time ({stats.base_win_rate:.0%}) quando há poucos deals. Aparece nos motivos, mas não entra no score: no histórico, não diferencia ganhos de perdidos. |

### Faixas
- 🟢 **Alta**, 🟡 **Média** e ⚪ **Baixa**: deals em *Engaging* dentro do ciclo normal (top 25%, próximos 35% e o restante).
- 🔵 **Qualificar**: deals em *Prospecting*, ainda sem data de engajamento.
- 🔴 **Requalificar**: mais de {CFG.stale_days} dias em *Engaging*. Nenhum deal do histórico fechou depois disso.

### O que os dados dizem (e o que não dizem)
- O **valor** é o que mais diferencia um deal do outro.
- **{(pipeline['band'] == 'Requalificar').sum()} deals ({(pipeline['band'] == 'Requalificar').mean():.0%} do pipeline aberto e {(pipeline.loc[pipeline['deal_stage'] == 'Engaging', 'band'] == 'Requalificar').mean():.0%} dos que estão em Engaging) estão parados** além do maior ciclo já visto. Limpar isso é o ganho mais imediato.
- **Nenhum atributo do CRM prevê se um deal será ganho ou perdido.** Vendedor, produto, conta, setor, região e tempo no pipeline acertam tanto quanto o acaso. Por isso a **Chance** é mostrada como informação, mas não pontua. O score é uma **regra de priorização**, não uma previsão.
"""
    )

    st.markdown("#### Quanto tempo os deals levam para fechar")
    closed = deals[deals["deal_stage"].isin(["Won", "Lost"])]
    hist = (
        closed.assign(
            semana=(closed["cycle_days"] // 7).astype(int),
            resultado=closed["deal_stage"].map({"Won": "Ganhos", "Lost": "Perdidos"}),
        )
        .groupby(["semana", "resultado"]).size().unstack(fill_value=0)
    )
    st.bar_chart(hist, x_label="Semanas entre engajamento e fechamento", y_label="Deals", stack=False)
    st.caption(
        f"Metade dos deals perdidos cai nas primeiras 2 semanas. Os ganhos fecham, em geral, entre "
        f"{stats.won_p25:.0f} e {stats.won_p75:.0f} dias. Nenhum deal passou de {CFG.stale_days} dias."
    )

    st.markdown("#### Validação com o passado")
    st.markdown(
        "Para cada fim de mês de 2017, reconstruímos os deals que estavam abertos naquele dia, "
        "calculamos o score só com o que se sabia até então e comparamos com o que aconteceu."
    )
    bt = backtest()
    mean = bt.drop(columns="snapshot").mean()
    auc_chance = f"{mean['auc_chance']:.2f}".replace(".", ",")
    auc_score = f"{mean['auc_score']:.2f}".replace(".", ",")
    b1, b2, b3 = st.columns(3)
    b1.metric("Valor ganho nos top 20% do score", f"{mean['captura_score']:.0%}")
    b2.metric("…se ordenasse só por valor", f"{mean['captura_so_valor']:.0%}")
    b3.metric("…em ordem aleatória", f"{mean['captura_aleatoria']:.0%}")
    st.markdown(
        f"""
- Os top 20% do score concentram **{mean['captura_score']:.0%}** do valor que acabou sendo ganho, contra
  **{mean['captura_aleatoria']:.0%}** ao acaso. Ordenar só por valor concentra {mean['captura_so_valor']:.0%}:
  o score abre mão de ~{(mean['captura_so_valor'] - mean['captura_score']) * 100:.0f} pontos para
  incluir o momento, e ganha a separação dos deals parados e uma ação por deal.
- **Por que a chance não pontua:** com os pesos 50/30/20, a chance só somava ruído. Os top 20%
  capturavam 46% do valor ganho; com 60/40/0, a captura subiu para 48% e foi maior em 8 de 9 meses.
- A capacidade de separar ganhos de perdidos (AUC) foi **{auc_chance}** para a chance e
  **{auc_score}** para o score total. 0,50 é cara ou coroa. Os dados disponíveis não
  permitem prever o resultado, e o app não finge que permitem.
"""
    )
    with st.expander("Resultado por mês"):
        st.dataframe(bt.round(3), hide_index=True, width="stretch")

    st.markdown(
        """
### Limitações
- Não há histórico de atividades (e-mails, ligações, reuniões), que é o sinal real de deal "esfriando".
- 68% dos deals abertos não têm conta no CRM; setor e porte não entram no score.
- O "hoje" é a última data do CRM (31/12/2017), configurável em `lead_scorer/config.py`.
"""
    )
