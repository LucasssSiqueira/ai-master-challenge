"""Lead Scorer — interface do vendedor. Só apresentação: regras de negócio ficam em lead_scorer/."""
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# Garante o import dos pacotes locais seja qual for o diretório de execução (e no AppTest de versões antigas).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from lead_scorer import insights  # noqa: E402
from lead_scorer.backtest import run_backtest  # noqa: E402
from lead_scorer.config import DEFAULT_CONFIG as CFG  # noqa: E402
from lead_scorer.data_loader import DataValidationError, load_deals  # noqa: E402
from lead_scorer.scoring import BAND_ORDER, build_priority_list  # noqa: E402
from ui import components as ui  # noqa: E402
from ui.theme import BAND_NAMES, CSS, GREEN, STONE  # noqa: E402

st.set_page_config(page_title="Lead Scorer", page_icon="🎯", layout="wide", initial_sidebar_state="collapsed")
st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)

SCOPES = {"Vendedor": "sales_agent", "Manager": "manager", "Região": "regional_office", "Time todo": None}
PAGE_IDS = [page for page, _, _ in ui.PAGES]


@st.cache_data
def load():
    deals = load_deals()
    pipeline, stats = build_priority_list(deals)
    pipeline["band"] = pipeline["band"].astype(str)
    return deals, pipeline, stats


@st.cache_data
def backtest():
    return run_backtest(load_deals())


try:
    deals, pipeline, stats = load()
except (FileNotFoundError, DataValidationError, ValueError) as error:
    st.error(
        "Não foi possível carregar os dados do CRM. Confira se os 4 CSVs estão em `solution/data/` "
        f"(veja o README).\n\nDetalhe: {error}"
    )
    st.stop()

# ---------- Estado vindo da URL (a navegação do rail é feita por links) ----------
def adopt_url(param: str, state_key: str, valid) -> None:
    """Se a URL mudou por fora (link do rail, prioridade clicada, recarga), ela manda no widget.

    O Streamlit reaproveita a sessão da aba ao recarregar, então o estado antigo do widget
    venceria a URL. Guardamos o último valor que nós mesmos escrevemos para diferenciar.
    """
    value = st.query_params.get(param)
    if value in valid and value != st.session_state.get(f"_url_{param}"):
        st.session_state[state_key] = value
        st.session_state[f"_url_{param}"] = value


page = st.query_params.get("page", "overview")
page = page if page in PAGE_IDS else "overview"

# ---------- Barra de escopo ----------
adopt_url("scope", "scope", SCOPES)
st.session_state.setdefault("scope", "Vendedor")
with st.container(key="topbar"):
    bar_left, bar_right = st.columns([2.2, 1], vertical_alignment="center")
with bar_left:
    scope = st.segmented_control(
        "Escopo", list(SCOPES), key="scope", label_visibility="collapsed"
    ) or "Vendedor"
column = SCOPES[scope]
who = None
if column:
    options = sorted(pipeline[column].unique())
    adopt_url("who", f"who_{scope}", options)
    with bar_right:
        who = st.selectbox(scope, options, key=f"who_{scope}", label_visibility="collapsed")
    df = pipeline[pipeline[column] == who]
else:
    df = pipeline

nav = {"page": page, "scope": scope, "who": who}
st.session_state["_url_scope"], st.session_state["_url_who"] = scope, who
st.query_params.update({k: v for k, v in nav.items() if v is not None})
if who is None and "who" in st.query_params:
    del st.query_params["who"]
st.markdown(ui.rail(page, nav), unsafe_allow_html=True)
scope_label = who or "Time todo"
greeting_name = ui.greeting_name(scope, who, CFG.viewer_name)


def deals_table(data: pd.DataFrame, key: str, show_band: bool = True) -> pd.Series | None:
    """Tabela com seleção de linha; devolve o deal selecionado.

    A seleção do Streamlit é guardada por posição de linha. A chave depende dos deals exibidos,
    então trocar de vendedor, visão ou faixa zera a seleção, em vez de apontar para outro deal
    ou para uma posição que não existe mais.
    """
    show = pd.DataFrame({
        "Faixa": data["band"].map(BAND_NAMES),
        "Score": data["score"],
        "Produto": data["product"],
        "Conta": data["account"].fillna("Não informada"),
        "Valor": data["sales_price"],
        "Dias": data["age_days"],
        "Vendedor": data["sales_agent"],
        "Próxima ação": data["action"],
    })
    if scope == "Vendedor":
        show = show.drop(columns="Vendedor")  # redundante: a tela inteira é de um vendedor
    if not show_band:
        show = show.drop(columns="Faixa")  # redundante numa página de uma faixa só
    event = st.dataframe(
        show,
        hide_index=True,
        width="stretch",
        height=min(36 * len(show) + 40, 520),
        on_select="rerun",
        selection_mode="single-row",
        key=f"{key}-{hash(tuple(data['opportunity_id']))}",
        column_config={
            "Score": st.column_config.ProgressColumn("Score", min_value=0, max_value=100, format="%d"),
            "Valor": st.column_config.NumberColumn("Valor (US$)", format="%d"),
            "Dias": st.column_config.NumberColumn("Dias engajado", format="%d"),
            "Próxima ação": st.column_config.TextColumn(width="large"),
        },
    )
    rows = event.selection.rows
    if not rows or rows[0] >= len(data):
        return None
    return data.iloc[rows[0]]


def deal_detail(row: pd.Series | None, hint: str) -> None:
    if row is None:
        st.caption(hint)
        return
    meters = [("Valor", row["score_value"], CFG.weight_value), ("Momento", row["score_timing"], CFG.weight_timing)]
    if CFG.weight_prob:
        meters.append(("Chance", row["score_prob"], CFG.weight_prob))
    with st.container(key="card_detail"):
        st.markdown(ui.detail_card(row, meters), unsafe_allow_html=True)


# ---------- Visão geral ----------
if page == "overview":
    st.markdown(ui.header(CFG.reference_date, greeting_name, insights.headline(df)), unsafe_allow_html=True)
    summary = insights.band_summary(df)
    with st.container(key="grid"):
        left, right = st.columns([1.2, 1], gap="medium")
    with left:
        with st.container(key="card_overview"):
            st.markdown(ui.overview_card(df, summary), unsafe_allow_html=True)
        with st.container(key="card_health"):
            st.markdown(ui.health_card(summary, insights.active_share(df)), unsafe_allow_html=True)
    with right:
        with st.container(key="card_priorities"):
            st.markdown(ui.priorities_card(insights.priorities(df), nav), unsafe_allow_html=True)
        with st.container(key="card_insight"):
            st.markdown(ui.insight_card(insights.main_insight(df, CFG.stale_days), nav), unsafe_allow_html=True)

# ---------- Pipeline ----------
elif page == "pipeline":
    active = df[df["band"] != "Requalificar"]
    st.markdown(ui.page_title("Pipeline", f"{len(active)} deals ativos · {scope_label}"), unsafe_allow_html=True)
    linked = active[active["opportunity_id"] == st.query_params.get("deal")]
    with st.container(key="card_pipeline"):
        bands = st.pills(
            "Faixas", [b for b in BAND_ORDER if b != "Requalificar"], selection_mode="multi",
            default=[b for b in BAND_ORDER if b != "Requalificar"], format_func=BAND_NAMES.get,
            key="bands", label_visibility="collapsed",
        )
        selected = deals_table(active[active["band"].isin(bands)], key="active")
    deal_detail(
        selected if selected is not None else (linked.iloc[0] if len(linked) else None),
        "Selecione um deal para ver por que ele tem esse score.",
    )

# ---------- Deals parados ----------
elif page == "requalify":
    stale = df[df["band"] == "Requalificar"].sort_values("sales_price", ascending=False)
    st.markdown(
        ui.page_title(
            "Deals parados",
            f"{len(stale)} deals há mais de {CFG.stale_days} dias em negociação, mais do que qualquer deal já fechado. "
            "Comece pelos de maior valor: confirme ou encerre.",
        ),
        unsafe_allow_html=True,
    )
    with st.container(key="card_stale"):
        selected = deals_table(stale, key="stale", show_band=False)
    deal_detail(selected, "Selecione um deal para ver os detalhes.")

# ---------- Como o score funciona ----------
else:
    active_all = pipeline[pipeline["band"].isin(["Alta", "Média", "Baixa"])]
    st.markdown(
        ui.page_title("Como o score funciona", "Uma regra de priorização transparente, validada com o passado."),
        unsafe_allow_html=True,
    )
    with st.container(key="card_method"):
        st.markdown(
            f"""
### O que o score mede

| Componente | Pontos | O que significa |
|---|---|---|
| **Valor** | até {CFG.weight_value:.0f} | Preço do produto em escala logarítmica. O GTK 500 custa ~490× o MG Special; sem o log, o score seria só "ordenar por valor". |
| **Momento** | até {CFG.weight_timing:.0f} | Máximo quando o deal está na janela em que os deals ganhos costumam fechar ({stats.won_p25:.0f}–{stats.won_p75:.0f} dias de engajamento). Cai depois disso e zera aos {CFG.stale_days} dias. |
| **Chance** | {CFG.weight_prob:.0f} (informativo) | Taxa de vitória do vendedor com aquele produto, puxada para a média do time ({stats.base_win_rate:.0%}) quando há poucos deals. Aparece nos motivos, mas não entra no score: no histórico, não diferencia ganhos de perdidos. |

### Faixas
- **Prioridade alta, média e baixa:** deals em *Engaging* dentro do ciclo normal. Alta = score no percentil 75 ou acima; média = entre os percentis 40 e 75; baixa = o restante. Scores empatados no corte ficam na faixa de cima, por isso a alta tem hoje {(active_all['band'] == 'Alta').mean():.0%} dos deals ativos, e não exatamente 25%.
- **Qualificar:** deals em *Prospecting*, ainda sem data de engajamento.
- **Parados:** mais de {CFG.stale_days} dias em *Engaging*. Nenhum deal do histórico fechou depois disso.

### O que os dados dizem (e o que não dizem)
- O **valor** é o que mais diferencia um deal do outro.
- **{(pipeline['band'] == 'Requalificar').sum()} deals ({(pipeline['band'] == 'Requalificar').mean():.0%} do pipeline aberto e {(pipeline.loc[pipeline['deal_stage'] == 'Engaging', 'band'] == 'Requalificar').mean():.0%} dos que estão em Engaging) estão parados** além do maior ciclo já visto. Limpar isso é o ganho mais imediato.
- **Nenhum atributo do CRM prevê se um deal será ganho ou perdido.** Vendedor, produto, conta, setor, região e tempo no pipeline acertam tanto quanto o acaso. Por isso a **chance** é mostrada como informação, mas não pontua. O score é uma **regra de priorização**, não uma previsão.
"""
        )

    with st.container(key="card_cycle"):
        st.markdown('<div class="ls-card-title">Quanto tempo os deals levam para fechar</div>', unsafe_allow_html=True)
        closed = deals[deals["deal_stage"].isin(["Won", "Lost"])]
        hist = (
            closed.assign(
                semana=(closed["cycle_days"] // 7).astype(int),
                resultado=closed["deal_stage"].map({"Won": "Ganhos", "Lost": "Perdidos"}),
            )
            .groupby(["semana", "resultado"]).size().unstack(fill_value=0)
        )
        st.bar_chart(
            hist, x_label="Semanas entre engajamento e fechamento", y_label="Deals", stack=False,
            color=[GREEN, STONE],
        )
        st.caption(
            f"Metade dos deals perdidos cai nas primeiras 2 semanas. Os ganhos fecham, em geral, entre "
            f"{stats.won_p25:.0f} e {stats.won_p75:.0f} dias. Nenhum deal passou de {CFG.stale_days} dias."
        )

    with st.container(key="card_backtest"):
        bt = backtest()
        mean = bt.drop(columns="snapshot").mean()
        auc_chance = f"{mean['auc_chance']:.2f}".replace(".", ",")
        auc_score = f"{mean['auc_score']:.2f}".replace(".", ",")
        tiles = "".join(
            f'<div class="ls-tile"><div class="ls-tile-label">{label}</div>'
            f'<div class="ls-tile-value">{value:.0%}</div></div>'
            for label, value in [
                ("Top 20% do score", mean["captura_score"]),
                ("Só por valor", mean["captura_so_valor"]),
                ("Ordem aleatória", mean["captura_aleatoria"]),
            ]
        )
        st.markdown(
            ui.compact(f"""
                <div class="ls-card-head"><span class="ls-card-title">Validação com o passado</span>
                <span class="ls-meta">valor ganho capturado</span></div>
                <div class="ls-tiles" style="grid-template-columns:1fr 1fr 1fr">{tiles}</div>
            """),
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
Para cada fim de mês de 2017, reconstruímos os deals abertos naquele dia, calculamos o score só com o que se sabia até então e comparamos com o que aconteceu.

- Os top 20% do score concentram **{mean['captura_score']:.0%}** do valor que acabou sendo ganho, contra **{mean['captura_aleatoria']:.0%}** ao acaso. Ordenar só por valor concentra {mean['captura_so_valor']:.0%}: o score abre mão de ~{(mean['captura_so_valor'] - mean['captura_score']) * 100:.0f} ponto para incluir o momento, e ganha a separação dos deals parados e uma ação por deal.
- **Por que a chance não pontua:** com os pesos 50/30/20, a chance só somava ruído. Os top 20% capturavam 46% do valor ganho; com 60/40/0, a captura subiu para 48% e foi maior em 8 de 9 meses.
- A capacidade de separar ganhos de perdidos (AUC) foi **{auc_chance}** para a chance e **{auc_score}** para o score total. 0,50 é cara ou coroa. Os dados disponíveis não permitem prever o resultado, e o app não finge que permitem.
"""
        )
        with st.expander("Resultado por mês"):
            st.dataframe(bt.round(3), hide_index=True, width="stretch")

    with st.container(key="card_limits"):
        st.markdown(
            f"""
### Limitações
- Não há histórico de atividades (e-mails, ligações, reuniões), que é o sinal real de deal "esfriando".
- 68% dos deals abertos não têm conta no CRM; setor e porte não entram no score.
- O "hoje" é {CFG.reference_date:%d/%m/%Y}, a última data do CRM, ajustável em `lead_scorer/config.py`.
"""
        )
