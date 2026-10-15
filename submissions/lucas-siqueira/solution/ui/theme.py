"""Tokens visuais, ícones Lucide e o CSS que adapta o Streamlit à identidade do produto."""

# ---- Tokens ----
BG = "#F2F3EC"
RAIL = "#101513"
CARD = "#FFFFFF"
TILE = "#F6F7F2"
INK = "#101513"
MUTED = "#6F746C"
FAINT = "#A4A89F"
LINE = "#ECEDE6"
GREEN = "#35D66B"
GREEN_INK = "#16803C"
GREEN_SOFT = "#E4F7EA"
AMBER = "#F0BE3A"
RED = "#E5544B"
RED_INK = "#B4342C"
RED_SOFT = "#FBE9E7"
SLATE = "#8D9AAE"
STONE = "#CBCEC4"

# Cor de cada faixa: só significado (verde = agir, âmbar = acompanhar, vermelho = parado).
BAND_COLORS = {
    "Alta": GREEN,
    "Média": AMBER,
    "Qualificar": SLATE,
    "Baixa": STONE,
    "Requalificar": RED,
}
BAND_NAMES = {
    "Alta": "Prioridade alta",
    "Média": "Prioridade média",
    "Qualificar": "Qualificar",
    "Baixa": "Prioridade baixa",
    "Requalificar": "Parados",
}

# ---- Ícones Lucide (24x24, traço 2) ----
_ICON_PATHS = {
    "layout-grid": '<rect width="7" height="7" x="3" y="3" rx="1"/><rect width="7" height="7" x="14" y="3" rx="1"/>'
                   '<rect width="7" height="7" x="14" y="14" rx="1"/><rect width="7" height="7" x="3" y="14" rx="1"/>',
    "list": '<path d="M3 12h.01"/><path d="M3 18h.01"/><path d="M3 6h.01"/><path d="M8 12h13"/>'
            '<path d="M8 18h13"/><path d="M8 6h13"/>',
    "rotate-ccw": '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>',
    "info": '<circle cx="12" cy="12" r="10"/><path d="M12 16v-4"/><path d="M12 8h.01"/>',
    "sparkles": '<path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 '
                '9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 '
                '.964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/>'
                '<path d="M22 5h-4"/>',
    "target": '<circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/>',
    "arrow-right": '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    "arrow-up-right": '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    "chevron-right": '<path d="m9 18 6-6-6-6"/>',
}


def icon(name: str, size: int = 20, stroke: float = 1.75) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
        f'stroke="currentColor" stroke-width="{stroke}" stroke-linecap="round" stroke-linejoin="round">'
        f'{_ICON_PATHS[name]}</svg>'
    )


LOGO = (
    '<svg width="22" height="22" viewBox="0 0 22 22" fill="none" xmlns="http://www.w3.org/2000/svg">'
    f'<rect x="2" y="12" width="4.2" height="8" rx="2.1" fill="{RAIL}"/>'
    f'<rect x="8.9" y="7" width="4.2" height="13" rx="2.1" fill="{RAIL}"/>'
    f'<rect x="15.8" y="2" width="4.2" height="18" rx="2.1" fill="{RAIL}"/></svg>'
)

RAIL_WIDTH = 88

CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap');

:root {{ --ls-font: 'Geist', 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; }}

html, body, [data-testid="stApp"], [data-testid="stApp"] *:not(svg):not(svg *) {{ font-family: var(--ls-font) !important; }}
/* Ícones do próprio Streamlit (setas do select, expander) usam uma fonte de símbolos: preservar. */
[data-testid="stApp"] [data-testid="stIconMaterial"], [data-testid="stApp"] .material-symbols-rounded {{
    font-family: 'Material Symbols Rounded' !important;
}}
[data-testid="stApp"] {{ background: {BG}; color: {INK}; }}
header[data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stSidebar"], [data-testid="stSidebarCollapsedControl"] {{ display: none !important; }}

[data-testid="stMainBlockContainer"], .block-container {{
    max-width: 1320px; padding: 36px 56px 72px calc({RAIL_WIDTH}px + 56px) !important;
}}

/* ---------- Rail ---------- */
.ls-rail {{
    position: fixed; inset: 0 auto 0 0; width: {RAIL_WIDTH}px; background: {RAIL}; z-index: 1000;
    display: flex; flex-direction: column; align-items: center; gap: 10px; padding-top: 28px;
}}
.ls-logo {{
    width: 48px; height: 48px; border-radius: 15px; background: {GREEN};
    display: flex; align-items: center; justify-content: center; margin-bottom: 26px;
}}
.ls-rail a {{
    width: 52px; height: 52px; border-radius: 16px; display: flex; align-items: center; justify-content: center;
    color: #DADDD5; opacity: .72; text-decoration: none; transition: background .15s, opacity .15s;
}}
.ls-rail a:hover {{ opacity: 1; background: rgba(255,255,255,.06); }}
.ls-rail a.active {{ background: {GREEN}; color: {RAIL}; opacity: 1; }}

/* ---------- Scope bar (segmented + select) ---------- */
.st-key-scope [data-testid="stButtonGroup"] > div {{
    background: {CARD}; border-radius: 999px; padding: 6px; gap: 2px; display: inline-flex;
}}
.st-key-scope button {{
    border: none !important; background: transparent !important; border-radius: 999px !important;
    padding: 10px 22px !important; min-height: 0 !important; color: {MUTED} !important; box-shadow: none !important;
}}
.st-key-scope button p {{ font-size: 15px !important; font-weight: 450; }}
.st-key-scope button[data-testid="stBaseButton-segmented_controlActive"],
.st-key-scope button[data-selected="true"] {{
    background: {INK} !important; color: #fff !important;
}}
.st-key-scope button[data-testid="stBaseButton-segmented_controlActive"] p,
.st-key-scope button[data-selected="true"], .st-key-scope button[data-selected="true"] * {{ color: #fff !important; }}
/* O seletor de vendedor vira uma pílula branca (cobre a marcação antiga e a nova do Streamlit). */
div[class*="st-key-who"] [data-testid="stSelectbox"] div[role="group"],
div[class*="st-key-who"] [data-baseweb="select"] > div {{
    background: {CARD} !important; border: none !important; border-radius: 999px !important;
    min-height: 50px; padding-left: 12px; box-shadow: none !important; cursor: pointer;
}}
div[class*="st-key-who"] [data-testid="stSelectbox"] * {{ font-size: 15px; color: {INK}; }}
div[class*="st-key-who"] {{ max-width: 300px; margin-left: auto; }}

/* ---------- Header ---------- */
.ls-date {{ font-size: 13px; letter-spacing: .08em; color: {MUTED}; text-transform: uppercase; margin: 34px 0 10px; }}
/* Sem o ícone de link que o Streamlit põe ao lado de títulos. */
[data-testid="stHeaderActionElements"], .ls-hello a, .ls-page-title a {{ display: none !important; }}
.ls-hello {{ font-size: 60px; line-height: 1.05; letter-spacing: -0.035em; font-weight: 500; color: {INK}; margin: 0; }}
.ls-lede {{ font-size: 19px; color: {MUTED}; margin: 16px 0 34px; }}
.ls-page-title {{ font-size: 40px; letter-spacing: -0.03em; font-weight: 500; margin: 34px 0 6px; }}

/* ---------- Cards ---------- */
div[class*="st-key-card"] {{
    background: {CARD}; border-radius: 30px; padding: 38px 40px 40px; gap: 0;
}}
.ls-card-head {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 22px; }}
.ls-card-title {{ font-size: 18px; font-weight: 500; color: {INK}; display: flex; align-items: center; gap: 10px; }}
.ls-card-title svg {{ color: {GREEN_INK}; }}
.ls-meta {{ font-size: 15px; color: {MUTED}; }}
.ls-big {{ font-size: 64px; line-height: 1; letter-spacing: -0.04em; font-weight: 450; color: {INK}; }}
.ls-big-row {{ display: flex; align-items: center; gap: 18px; }}
.ls-sub {{ font-size: 15px; color: {MUTED}; margin: 14px 0 30px; }}
.ls-chip {{
    display: inline-flex; align-items: center; gap: 6px; padding: 8px 16px; border-radius: 999px;
    font-size: 15px; font-weight: 500;
}}
.ls-chip.good {{ background: {GREEN_SOFT}; color: {GREEN_INK}; }}
.ls-chip.bad {{ background: {RED_SOFT}; color: {RED_INK}; }}

.ls-tiles {{ display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }}
.ls-tile {{ background: {TILE}; border-radius: 20px; padding: 22px 24px; }}
.ls-tile-label {{ display: flex; align-items: center; gap: 10px; font-size: 15px; color: {MUTED}; }}
.ls-tile-value {{ margin-top: 14px; font-size: 26px; letter-spacing: -0.02em; font-weight: 500; color: {INK}; white-space: nowrap; }}
.ls-tile-value small {{ font-size: 15px; font-weight: 400; color: {FAINT}; margin-left: 8px; letter-spacing: 0; }}
.ls-dot {{ width: 9px; height: 9px; border-radius: 50%; display: inline-block; flex: none; }}

.ls-bar {{ display: flex; gap: 6px; margin: 30px 0 14px; }}
.ls-bar span {{ height: 12px; border-radius: 999px; }}
.ls-rows {{ margin-top: 10px; }}
.ls-row {{ display: flex; align-items: center; gap: 14px; padding: 17px 0; border-bottom: 1px solid {LINE}; font-size: 16px; }}
.ls-row:last-child {{ border-bottom: none; }}
.ls-row .name {{ flex: 1; color: {INK}; }}
.ls-row .count {{ color: {FAINT}; }}
.ls-row .value {{ min-width: 92px; text-align: right; font-weight: 500; }}

/* ---------- Priorities ---------- */
.ls-prio {{ display: flex; flex-direction: column; gap: 10px; }}
.ls-prio a {{
    display: flex; align-items: center; gap: 20px; padding: 20px 22px; background: {TILE}; border-radius: 20px;
    text-decoration: none !important; color: {INK} !important; transition: background .15s;
}}
.ls-prio a:hover {{ background: #EEEFE8; }}
.ls-prio .num {{ font-size: 15px; color: {FAINT}; width: 22px; font-variant-numeric: tabular-nums; }}
.ls-prio .body {{ flex: 1; min-width: 0; }}
.ls-prio .title {{ font-size: 16px; font-weight: 500; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
.ls-prio .why {{ font-size: 14px; color: {MUTED}; margin-top: 4px; display: flex; align-items: center; gap: 8px; white-space: nowrap; overflow: hidden; }}
.ls-prio .why span:last-child {{ overflow: hidden; text-overflow: ellipsis; }}
.ls-prio .score {{ font-size: 28px; letter-spacing: -0.03em; font-weight: 450; font-variant-numeric: tabular-nums; }}
.ls-empty {{ background: {TILE}; border-radius: 20px; padding: 26px; color: {MUTED}; font-size: 15px; }}

/* ---------- Insight ---------- */
.ls-insight-label {{ font-size: 16px; color: {MUTED}; margin-top: 10px; }}
.ls-insight-detail {{ font-size: 15px; color: {MUTED}; line-height: 1.55; margin: 22px 0 24px; }}
.ls-action {{ background: {TILE}; border-radius: 20px; padding: 20px 22px; display: flex; gap: 14px; align-items: flex-start; }}
.ls-action svg {{ color: {GREEN_INK}; flex: none; margin-top: 2px; }}
.ls-action div {{ font-size: 15px; line-height: 1.5; }}
.ls-cta {{
    display: inline-flex; align-items: center; gap: 8px; margin-top: 22px; padding: 13px 22px; border-radius: 999px;
    background: {INK}; color: #fff !important; text-decoration: none !important; font-size: 15px; font-weight: 500;
}}
.ls-cta:hover {{ background: #232A26; }}

/* ---------- Detail ---------- */
.ls-detail-head {{ display: flex; justify-content: space-between; align-items: flex-start; gap: 24px; }}
.ls-detail-title {{ font-size: 22px; font-weight: 500; letter-spacing: -0.02em; }}
.ls-detail-meta {{ font-size: 14px; color: {MUTED}; margin-top: 6px; }}
.ls-meter {{ margin-top: 18px; }}
.ls-meter-label {{ display: flex; justify-content: space-between; font-size: 14px; color: {MUTED}; margin-bottom: 8px; }}
.ls-meter-track {{ height: 8px; background: {TILE}; border-radius: 999px; overflow: hidden; }}
.ls-meter-fill {{ height: 100%; background: {GREEN}; border-radius: 999px; }}
.ls-reasons {{ list-style: none; padding: 0; margin: 4px 0 0; }}
.ls-reasons li {{ display: flex; gap: 12px; align-items: flex-start; padding: 10px 0; font-size: 15px; line-height: 1.5; }}
.ls-reasons .ls-dot {{ margin-top: 7px; }}

/* ---------- Widgets dentro dos cards ---------- */
div[class*="st-key-card"] [data-testid="stDataFrame"] {{ border-radius: 16px; overflow: hidden; }}
.st-key-bands button {{
    border-radius: 999px !important; border: 1px solid {LINE} !important; background: {CARD} !important;
    box-shadow: none !important;
}}
.st-key-bands button[data-testid="stBaseButton-pillsActive"], .st-key-bands button[data-selected="true"] {{
    background: {INK} !important; border-color: {INK} !important;
}}
.st-key-bands button {{ color: {MUTED} !important; padding: 8px 16px !important; }}
.st-key-bands button[data-testid="stBaseButton-pillsActive"] *, .st-key-bands button[data-selected="true"],
.st-key-bands button[data-selected="true"] * {{ color: #fff !important; }}
[data-testid="stMetricValue"] {{ font-weight: 450; letter-spacing: -0.03em; }}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] {{ font-size: 15px; line-height: 1.65; }}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] h3 {{
    font-size: 18px; font-weight: 500; letter-spacing: -0.01em; margin: 26px 0 10px; padding: 0;
}}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] h3:first-child {{ margin-top: 0; }}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] table {{ width: 100%; border-collapse: collapse; border: none; }}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] th,
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] td {{
    text-align: left; padding: 12px 12px 12px 0; border: none; border-bottom: 1px solid {LINE}; vertical-align: top;
}}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] th {{ font-weight: 500; color: {MUTED}; font-size: 14px; }}
div[class*="st-key-card"] [data-testid="stMarkdownContainer"] li {{ margin-bottom: 6px; }}
div[class*="st-key-card"] [data-testid="stExpander"] details {{ border: 1px solid {LINE}; border-radius: 16px; }}

/* ---------- Responsivo ---------- */
.st-key-scope [data-testid="stButtonGroup"] > div {{ flex-wrap: wrap; }}
@media (max-width: 1180px) {{
    .st-key-grid [data-testid="stHorizontalBlock"] {{ flex-direction: column; gap: 16px; }}
    .st-key-grid [data-testid="stColumn"] {{
        width: 100% !important; flex: 1 1 100% !important; min-width: 100% !important;
    }}
    /* Empilhado, a coluna da direita (prioridades e insight) vem primeiro: é o que pede ação. */
    .st-key-grid [data-testid="stColumn"]:nth-child(2) {{ order: -1; }}
    .st-key-topbar [data-testid="stHorizontalBlock"] {{ flex-wrap: wrap; }}
    .st-key-topbar [data-testid="stColumn"] {{
        flex: 1 1 auto !important; width: auto !important; min-width: 0 !important;
    }}
}}
@media (max-width: 760px) {{
    [data-testid="stMainBlockContainer"], .block-container {{
        padding: 24px 16px 48px calc({RAIL_WIDTH}px + 16px) !important;
    }}
    div[class*="st-key-card"] {{ padding: 28px 24px; border-radius: 24px; }}
    .ls-hello {{ font-size: 40px; }}
    .ls-big {{ font-size: 52px; }}
    .ls-tiles {{ grid-template-columns: 1fr; }}
}}
"""
