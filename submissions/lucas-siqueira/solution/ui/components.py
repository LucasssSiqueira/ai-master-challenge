"""Blocos de HTML da interface. Funções puras: recebem dados, devolvem HTML (testáveis sem Streamlit).

Regra: todo texto vindo dos dados passa por `esc`. O HTML sai em uma linha, sem indentação,
para o Markdown do Streamlit não o transformar em bloco de código.
"""
from html import escape
from urllib.parse import urlencode

import pandas as pd

from lead_scorer.explain import money, money_short
from lead_scorer.insights import Insight

from .theme import BAND_COLORS, BAND_NAMES, LOGO, icon

WEEKDAYS = ["segunda-feira", "terça-feira", "quarta-feira", "quinta-feira", "sexta-feira", "sábado", "domingo"]
MONTHS = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto",
          "setembro", "outubro", "novembro", "dezembro"]

PAGES = [  # (id, rótulo, ícone)
    ("overview", "Visão geral", "layout-grid"),
    ("pipeline", "Pipeline", "list"),
    ("requalify", "Deals parados", "rotate-ccw"),
    ("method", "Como o score funciona", "info"),
]

# Prefixo dos motivos (explain.py) -> cor do ponto na interface.
REASON_DOT = {"✅": BAND_COLORS["Alta"], "⚠️": BAND_COLORS["Requalificar"], "➖": "#CBCEC4", "ℹ️": "#CBCEC4"}


def esc(value) -> str:
    return escape(str(value), quote=True)


def compact(html: str) -> str:
    return "".join(line.strip() for line in html.splitlines())


def link(params: dict) -> str:
    return "?" + urlencode({k: v for k, v in params.items() if v is not None})


def date_label(day: pd.Timestamp) -> str:
    return f"{WEEKDAYS[day.weekday()]}, {day.day} de {MONTHS[day.month - 1]} de {day.year}"


def dot(color: str) -> str:
    return f'<span class="ls-dot" style="background:{color}"></span>'


def rail(active: str, params: dict) -> str:
    items = "".join(
        f'<a href="{esc(link({**params, "page": page}))}" target="_self" title="{esc(label)}" '
        f'class="{"active" if page == active else ""}">{icon(name, 22)}</a>'
        for page, label, name in PAGES
    )
    return f'<nav class="ls-rail"><div class="ls-logo">{LOGO}</div>{items}</nav>'


def greeting_name(scope: str, who: str | None, fallback: str) -> str:
    """Primeiro nome do vendedor ou manager em foco; em Região e Time todo, quem usa o app."""
    return who.split()[0] if who and scope in ("Vendedor", "Manager") else fallback


def header(day: pd.Timestamp, viewer: str, lede: str) -> str:
    return compact(f"""
        <div class="ls-date">{esc(date_label(day))}</div>
        <h1 class="ls-hello">Good morning, {esc(viewer)}</h1>
        <p class="ls-lede">{esc(lede)}</p>
    """)


def page_title(title: str, lede: str) -> str:
    return compact(f'<h1 class="ls-page-title">{esc(title)}</h1><p class="ls-lede">{esc(lede)}</p>')


def overview_card(df: pd.DataFrame, summary: pd.DataFrame) -> str:
    tiles = "".join(
        f'<div class="ls-tile"><div class="ls-tile-label">{dot(BAND_COLORS[b])}{esc(BAND_NAMES[b])}</div>'
        f'<div class="ls-tile-value">{money_short(summary.loc[b, "value"])}'
        f'<small>{int(summary.loc[b, "deals"])} deals</small></div></div>'
        for b in ["Alta", "Média", "Qualificar", "Requalificar"]
    )
    return compact(f"""
        <div class="ls-card-head"><span class="ls-card-title">Pipeline aberto</span></div>
        <div class="ls-big">{len(df)}</div>
        <div class="ls-sub">deals abertos · {money_short(df["sales_price"].sum())} em preço de lista</div>
        <div class="ls-tiles">{tiles}</div>
    """)


def health_card(summary: pd.DataFrame, active_share: float) -> str:
    stale = int(summary.loc["Requalificar", "deals"])
    chip = (f'<span class="ls-chip bad">{stale} parados</span>' if active_share < 0.5
            else f'<span class="ls-chip good">pipeline em dia</span>')
    bar = "".join(
        f'<span style="flex:{row.share:.4f};background:{BAND_COLORS[band]}"></span>'
        for band, row in summary.iterrows() if row.deals
    )
    rows = "".join(
        f'<div class="ls-row">{dot(BAND_COLORS[band])}<span class="name">{esc(BAND_NAMES[band])}</span>'
        f'<span class="count">{int(row.deals)} deals</span><span class="value">{money_short(row.value)}</span></div>'
        for band, row in summary.iterrows()
    )
    return compact(f"""
        <div class="ls-card-head"><span class="ls-card-title">Saúde do pipeline</span>
        <span class="ls-meta">por número de deals</span></div>
        <div class="ls-big-row"><span class="ls-big">{active_share:.0%}</span>{chip}</div>
        <div class="ls-sub" style="margin-bottom:0">dos deals estão ativos, dentro do ciclo normal de venda</div>
        <div class="ls-bar">{bar}</div>
        <div class="ls-rows">{rows}</div>
    """)


def priorities_card(top: pd.DataFrame, params: dict) -> str:
    if top.empty:
        items = '<div class="ls-empty">Nenhum deal ativo. Comece pelos deals parados.</div>'
    else:
        items = "".join(
            f'<a href="{esc(link({**params, "page": "pipeline", "deal": row.opportunity_id}))}" target="_self" '
            f'aria-label="{esc(f"Abrir deal {i}: {row.product}, score {row.score}")}">'
            f'<span class="num">{i:02d}</span><div class="body">'
            f'<div class="title">{esc(row.product)}{" · " + esc(row.account) if isinstance(row.account, str) else ""}</div>'
            f'<div class="why">{dot(BAND_COLORS[row.band])}<span>{money_short(row.sales_price)} · {esc(row.short_reason)}</span></div>'
            f'</div><span class="score">{row.score}</span></a>'
            for i, row in enumerate(top.itertuples(index=False), start=1)
        )
    return compact(f"""
        <div class="ls-card-head"><span class="ls-card-title">{icon("target", 20)}Prioridades de hoje</span>
        <span class="ls-meta">score</span></div>
        <div class="ls-prio">{items}</div>
    """)


def insight_card(insight: Insight, params: dict) -> str:
    return compact(f"""
        <div class="ls-card-head"><span class="ls-card-title">{icon("sparkles", 20)}Insight do dia</span></div>
        <div class="ls-big">{esc(insight.metric)}</div>
        <div class="ls-insight-label">{esc(insight.label)}</div>
        <div class="ls-insight-detail">{esc(insight.detail)}</div>
        <div class="ls-action">{icon("arrow-right", 18)}<div>{esc(insight.action)}</div></div>
        <a class="ls-cta" href="{esc(link({**params, "page": insight.page}))}" target="_self">{esc(insight.cta)}{icon("arrow-up-right", 16)}</a>
    """)


def split_reason(reason: str) -> tuple[str, str]:
    """'✅ Texto' -> (cor do ponto, 'Texto'). Os ícones do texto viram pontos coloridos."""
    for prefix, color in REASON_DOT.items():
        if reason.startswith(prefix):
            return color, reason[len(prefix):].strip()
    return REASON_DOT["➖"], reason


def detail_card(row: pd.Series, meters: list[tuple[str, float, float]]) -> str:
    account = row["account"] if isinstance(row["account"], str) else "Conta não informada"
    bars = "".join(
        f'<div class="ls-meter"><div class="ls-meter-label"><span>{esc(label)}</span>'
        f'<span>{pts:.0f} de {weight:.0f}</span></div><div class="ls-meter-track">'
        f'<div class="ls-meter-fill" style="width:{min(pts / weight, 1) * 100:.1f}%"></div></div></div>'
        for label, pts, weight in meters
    )
    reasons = "".join(f"<li>{dot(c)}<span>{esc(t)}</span></li>" for c, t in map(split_reason, row["reasons"]))
    return compact(f"""
        <div class="ls-detail-head"><div>
        <div class="ls-detail-title">{esc(row["product"])} · {esc(account)}</div>
        <div class="ls-detail-meta">{money(row["sales_price"])} · {esc(BAND_NAMES[row["band"]])} · {esc(row["sales_agent"])} · ID {esc(row["opportunity_id"])}</div>
        </div><div class="ls-big" style="font-size:52px">{row["score"]}</div></div>
        <div class="ls-action" style="margin-top:24px">{icon("arrow-right", 18)}<div>{esc(row["action"])}</div></div>
        <div style="display:grid;grid-template-columns:1fr 1.4fr;gap:40px;margin-top:10px">
        <div>{bars}</div><ul class="ls-reasons" style="margin-top:12px">{reasons}</ul></div>
    """)
