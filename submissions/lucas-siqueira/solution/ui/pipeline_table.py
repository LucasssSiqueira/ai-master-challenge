"""Tabela interativa de deals (Pipeline e Deals parados).

Busca, filtros, ordenação, paginação e o painel de detalhes rodam no navegador, dentro de um
único componente HTML. Assim, nenhuma interação recarrega a página e o vendedor não perde o
contexto. O Python só entrega os dados reais do recorte atual, sem recalcular nada.
"""
import json
import math

import pandas as pd

from .components import split_reason
from .theme import (
    AMBER, BAND_COLORS, BG, CARD, FAINT, GREEN, GREEN_INK, INK, LINE, MUTED, RAIL, RED, SLATE, STONE, TILE, _ICON_PATHS,
)

PRIORITY_LABELS = {
    "Alta": "Alta prioridade",
    "Média": "Média prioridade",
    "Qualificar": "Qualificar",
    "Baixa": "Baixa prioridade",
    "Requalificar": "Parado",
}
STAGE_LABELS = {"Engaging": "Em negociação", "Prospecting": "Prospecção"}
ICONS = ["search", "sliders-horizontal", "x", "chevron-down", "arrow-down-up", "check", "chevron-left", "chevron-right",
         "arrow-right"]


def _num(value):
    return None if value is None or (isinstance(value, float) and math.isnan(value)) else value


def records(df: pd.DataFrame) -> list[dict]:
    """Uma linha por deal, na ordem padrão recebida (prioridade operacional)."""
    rows = []
    for rank, row in enumerate(df.itertuples(index=False)):
        account = row.account if isinstance(row.account, str) else None
        rows.append({
            "id": row.opportunity_id,
            "rank": rank,
            "account": account,
            "product": row.product,
            "value": int(row.sales_price),
            "stage": STAGE_LABELS.get(row.deal_stage, row.deal_stage),
            "band": row.band,
            "priority": PRIORITY_LABELS[row.band],
            "color": BAND_COLORS[row.band],
            "score": int(row.score),
            "pv": round(float(row.score_value)),
            "pm": round(float(row.score_timing)),
            "age": None if _num(row.age_days) is None else int(row.age_days),
            "seller": row.sales_agent,
            "manager": row.manager,
            "region": row.regional_office,
            "short": row.short_reason,
            "action": row.action,
            "reasons": [list(split_reason(r)) for r in row.reasons],
            "crm": account is None,
            "dup": bool(row.possible_duplicate),
        })
    return rows


def _json(data) -> str:
    # "</" fecharia o <script> antes da hora: dados nunca saem do JSON.
    return json.dumps(data, ensure_ascii=False).replace("</", "<\\/")


def render(df: pd.DataFrame, *, title: str, noun: str, scope_label: str, show_seller: bool,
           show_priority: bool, default_sort: str, initial_deal: str | None,
           weights: tuple[float, float]) -> str:
    """Documento HTML completo do componente."""
    config = {
        "title": title, "noun": noun, "scope": scope_label, "showSeller": show_seller,
        "showPriority": show_priority, "defaultSort": default_sort, "initialDeal": initial_deal,
        "weights": list(weights), "pageSize": 50,
        "priorities": [PRIORITY_LABELS[b] for b in ["Alta", "Média", "Qualificar", "Baixa", "Requalificar"]
                       if b in set(df["band"])],
        "sellers": sorted(df["sales_agent"].unique().tolist()),
        "stages": [s for s in ["Em negociação", "Prospecção"] if s in {STAGE_LABELS[x] for x in df["deal_stage"]}],
        "products": sorted(df["product"].unique().tolist()),
    }
    icons = {name: _ICON_PATHS[name] for name in ICONS}
    css = _CSS
    for token, value in {"BG": BG, "CARD": CARD, "INK": INK, "MUTED": "#69716B", "FAINT": FAINT, "LINE": LINE,
                         "TILE": TILE, "GREEN": GREEN, "GREEN_INK": GREEN_INK, "RAIL": RAIL, "RED": RED,
                         "AMBER": AMBER, "SLATE": SLATE, "STONE": STONE}.items():
        css = css.replace(f"--{token}--", value)
    return (_TEMPLATE.replace("/*CSS*/", css)
            .replace("__DATA__", _json(records(df)))
            .replace("__CONFIG__", _json(config))
            .replace("__ICONS__", _json(icons)))


_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;background:--BG--;color:--INK--;font-family:'Geist','Inter',-apple-system,BlinkMacSystemFont,sans-serif;
  font-size:14px;-webkit-font-smoothing:antialiased}
body{display:flex;flex-direction:column;overflow:hidden}
button,input{font:inherit;color:inherit}
svg{flex:none}
.head{padding:4px 2px 18px}
.head h1{font-size:32px;font-weight:500;letter-spacing:-.03em;line-height:1.1}
.head p{margin-top:8px;color:--MUTED--;font-size:15px}
.card{flex:1;min-height:0;display:flex;flex-direction:column;background:--CARD--;border-radius:24px;
  box-shadow:0 1px 2px rgba(16,21,19,.04)}
.toolbar{display:flex;gap:8px;align-items:center;flex-wrap:wrap;padding:18px 20px 14px}
.search{flex:1 1 240px;max-width:340px;display:flex;align-items:center;gap:8px;height:36px;padding:0 12px;
  background:--TILE--;border:1px solid transparent;border-radius:10px;transition:border-color .15s,background .15s}
.search:focus-within{background:#fff;border-color:--LINE--;box-shadow:0 0 0 3px rgba(53,214,107,.15)}
.search svg{color:--MUTED--}
.search input{flex:1;min-width:0;border:none;outline:none;background:transparent;font-size:14px}
.search input::placeholder{color:--FAINT--}
.fbtn{position:relative;display:inline-flex;align-items:center;gap:6px;height:36px;padding:0 12px;border-radius:10px;
  border:1px solid --LINE--;background:#fff;color:--INK--;cursor:pointer;font-size:14px;white-space:nowrap;
  transition:background .15s,border-color .15s}
.fbtn:hover{background:--TILE--}
.fbtn svg{color:--MUTED--}
.fbtn.on{background:#EDF9F1;border-color:#BFEBCD;color:--GREEN_INK--}
.fbtn.on svg{color:--GREEN_INK--}
.fbtn .n{min-width:18px;height:18px;padding:0 5px;border-radius:9px;background:--GREEN_INK--;color:#fff;font-size:11px;
  display:inline-flex;align-items:center;justify-content:center;font-variant-numeric:tabular-nums}
.clear{height:36px;padding:0 8px;border:none;background:none;color:--MUTED--;cursor:pointer;display:none;
  align-items:center;gap:4px;font-size:14px}
.clear:hover{color:--INK--}
.clear.show{display:inline-flex}
.spacer{flex:1}
.sort{display:inline-flex;align-items:center;gap:6px;color:--MUTED--;font-size:14px;white-space:nowrap}
.sort .fbtn{border-color:transparent;background:transparent;padding:0 8px}
.sort .fbtn:hover{background:--TILE--}
.menu{position:absolute;top:42px;left:0;z-index:30;min-width:220px;max-height:300px;overflow:auto;padding:6px;
  background:#fff;border:1px solid --LINE--;border-radius:12px;box-shadow:0 8px 24px rgba(16,21,19,.08);display:none}
.menu.right{left:auto;right:0}
.menu.open{display:block;animation:pop .12s ease-out}
.menu h4{font-size:12px;font-weight:500;color:--MUTED--;padding:8px 8px 4px}
.opt{display:flex;align-items:center;gap:10px;width:100%;padding:8px;border:none;background:none;border-radius:8px;
  cursor:pointer;text-align:left;font-size:14px}
.opt:hover{background:--TILE--}
.box{width:16px;height:16px;border-radius:5px;border:1px solid #CFD3CA;display:flex;align-items:center;justify-content:center}
.opt.sel .box{background:--INK--;border-color:--INK--;color:#fff}
.opt .dot{margin-left:-2px}
@keyframes pop{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:none}}

.grid{flex:1;min-height:0;overflow:auto;border-top:1px solid --LINE--}
.row{display:grid;align-items:center;column-gap:16px;padding:0 20px;min-height:58px;border-bottom:1px solid #F1F2EC;
  cursor:pointer;transition:background .12s}
.cols{grid-template-columns:minmax(180px,2.2fr) 112px 72px 148px minmax(100px,1fr) 92px 56px minmax(140px,1.9fr) 16px}
.hdr{position:sticky;top:0;z-index:5;min-height:40px;background:#fff;cursor:default;border-bottom:1px solid --LINE--}
.hdr .c{font-size:12px;color:--MUTED--;font-weight:500}
.hdr .c.s{cursor:pointer;user-select:none;display:flex;gap:4px;align-items:center}
.hdr .c.s:hover{color:--INK--}
.hdr .c.act{color:--INK--}
.hdr .c.r{justify-content:flex-end}
.body .row:hover{background:#FAFBF7}
.body .row:focus-visible{outline:2px solid rgba(53,214,107,.5);outline-offset:-2px}
.body .row.cur{background:#F4FBF6}
.c{min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.r{text-align:right}
.num{font-variant-numeric:tabular-nums}
.acc b{display:block;font-weight:500;overflow:hidden;text-overflow:ellipsis}
.acc b.none{color:--MUTED--;font-weight:400}
.acc span{display:block;font-size:12px;color:--FAINT--;margin-top:2px;overflow:hidden;text-overflow:ellipsis}
.score{display:flex;align-items:center;gap:8px}
.score strong{font-size:15px;font-weight:500;width:22px;text-align:right}
.meter{width:28px;height:4px;border-radius:2px;background:#ECEEE8;overflow:hidden}
.meter i{display:block;height:100%;border-radius:2px}
.prio{display:flex;align-items:center;gap:8px}
.dot{width:8px;height:8px;border-radius:50%;display:inline-block;flex:none}
.muted{color:--MUTED--}
.act{color:--MUTED--}
.chev{color:#C4C8BF}
.tag{display:inline-block;margin-left:6px;padding:1px 6px;border-radius:6px;background:#FFF4F2;color:#B4342C;font-size:11px;
  font-weight:500;vertical-align:1px}

.foot{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 20px;border-top:1px solid --LINE--;
  color:--MUTED--;font-size:13px}
.pager{display:flex;gap:4px}
.pager button{width:32px;height:32px;border-radius:8px;border:1px solid --LINE--;background:#fff;cursor:pointer;
  display:flex;align-items:center;justify-content:center}
.pager button:disabled{opacity:.35;cursor:default}

.empty{padding:72px 20px;text-align:center;color:--MUTED--}
.empty svg{color:--FAINT--;margin-bottom:12px}
.empty b{display:block;color:--INK--;font-weight:500;font-size:15px;margin-bottom:6px}
.empty button{margin-top:16px;height:34px;padding:0 14px;border-radius:10px;border:1px solid --LINE--;background:#fff;cursor:pointer}

.tip{position:fixed;z-index:60;max-width:280px;padding:10px 12px;border-radius:10px;background:--RAIL--;color:#fff;
  font-size:12.5px;line-height:1.5;pointer-events:none;opacity:0;transform:translateY(2px);transition:opacity .12s,transform .12s}
.tip.show{opacity:1;transform:none}
.tip .t{font-weight:500;margin-bottom:4px}
.tip .l{display:flex;justify-content:space-between;gap:16px;color:#C9CEC6}

.shade{position:fixed;inset:0;z-index:40;background:rgba(16,21,19,.12);opacity:0;pointer-events:none;transition:opacity .18s}
.shade.open{opacity:1;pointer-events:auto}
/* Fechado: sem sombra e invisível (a sombra vazava na borda direita). */
.drawer{position:fixed;top:0;right:0;bottom:0;z-index:50;width:min(440px,100%);background:#fff;
  transform:translateX(100%);visibility:hidden;
  transition:transform .22s cubic-bezier(.2,.8,.2,1),visibility 0s linear .22s,box-shadow .22s;
  display:flex;flex-direction:column}
.drawer.open{transform:none;visibility:visible;box-shadow:-8px 0 30px rgba(16,21,19,.08);
  transition:transform .22s cubic-bezier(.2,.8,.2,1),visibility 0s,box-shadow .22s}
.dh{display:flex;align-items:flex-start;justify-content:space-between;gap:16px;padding:24px 24px 16px}
.dh h2{font-size:20px;font-weight:500;letter-spacing:-.02em;line-height:1.25}
.dh p{margin-top:6px;color:--MUTED--;font-size:13px}
.x{width:34px;height:34px;border-radius:10px;border:none;background:--TILE--;cursor:pointer;display:flex;align-items:center;
  justify-content:center;flex:none}
.x:hover{background:#ECEDE6}
.db{flex:1;overflow:auto;padding:0 24px 28px}
.big{display:flex;align-items:baseline;gap:12px;margin:6px 0 18px}
.big strong{font-size:48px;font-weight:450;letter-spacing:-.04em;line-height:1}
.facts{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:--LINE--;border:1px solid --LINE--;border-radius:14px;overflow:hidden}
.facts div{background:#fff;padding:12px 14px}
.facts dt{font-size:12px;color:--MUTED--}
.facts dd{margin-top:3px;font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.sec{margin-top:24px}
.sec h3{font-size:12px;font-weight:500;color:--MUTED--;text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px}
.rec{display:flex;gap:10px;padding:14px 16px;border-radius:14px;background:#F2FAF4;color:--INK--;line-height:1.5}
.rec svg{color:--GREEN_INK--;margin-top:2px}
.bar{margin-bottom:12px}
.bar .lab{display:flex;justify-content:space-between;font-size:13px;color:--MUTED--;margin-bottom:6px}
.bar .trk{height:6px;border-radius:3px;background:--TILE--;overflow:hidden}
.bar .trk i{display:block;height:100%;background:--GREEN--;border-radius:3px}
.rs{list-style:none}
.rs li{display:flex;gap:10px;padding:7px 0;line-height:1.5}
.rs .dot{margin-top:7px}

/* Tablet: só o essencial. */
@media (max-width:1000px){
  .cols{grid-template-columns:minmax(160px,2fr) 72px 140px 88px minmax(120px,1.6fr) 16px}
  .c-stage,.c-product,.c-age{display:none !important}
  .sort .lbl{display:none}
}
/* Mobile: linhas compactas, sem rolagem horizontal. */
@media (max-width:640px){
  .head h1{font-size:26px}
  .toolbar{padding:14px}
  .search{max-width:none;flex-basis:100%}
  .hdr{display:none}
  .row.cols{grid-template-columns:1fr auto;grid-template-areas:"acc score" "meta meta" "act act";row-gap:4px;padding:14px;min-height:0}
  .c-acc{grid-area:acc}.c-score{grid-area:score}.c-prio{grid-area:meta}.c-act{grid-area:act;font-size:13px}
  .c-value,.c-chev{display:none !important}
  .c-prio .val{display:inline;color:--MUTED--}
  .foot{padding:12px 14px}
}
.c-prio .val{display:none}
"""

_TEMPLATE = """<!doctype html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&display=swap" rel="stylesheet">
<style>/*CSS*/</style></head>
<body>
<header class="head"><h1 id="title"></h1><p id="count" aria-live="polite"></p></header>
<section class="card">
  <div class="toolbar" id="toolbar"></div>
  <div class="grid" id="grid" role="table" aria-label="Deals">
    <div class="row cols hdr" role="row" id="hdr"></div>
    <div class="body" id="body" role="rowgroup"></div>
  </div>
  <div class="foot"><span id="range"></span><div class="pager"><button id="prev" aria-label="Página anterior"></button><button id="next" aria-label="Próxima página"></button></div></div>
</section>
<div class="tip" id="tip" role="tooltip"></div>
<div class="shade" id="shade"></div>
<aside class="drawer" id="drawer" role="dialog" aria-modal="true" aria-labelledby="dtitle" aria-hidden="true"></aside>
<script>
const DATA = __DATA__;
const CFG = __CONFIG__;
const ICON_PATHS = __ICONS__;
const icon = (n, s = 16) => `<svg width="${s}" height="${s}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICON_PATHS[n]}</svg>`;
const esc = v => String(v ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const money = v => "US$ " + v.toLocaleString("pt-BR");
const plural = (n, one, many) => `${n.toLocaleString("pt-BR")} ${n === 1 ? one : many}`;
const norm = s => String(s ?? "").normalize("NFD").replace(/[\\u0300-\\u036f]/g, "").toLowerCase();

// ---------- Estado ----------
const SORTS = {
  priority: {label: "Prioridade", key: d => d.rank, dir: "asc"},
  score: {label: "Score", key: d => d.score, dir: "desc"},
  value: {label: "Valor", key: d => d.value, dir: "desc"},
  age: {label: "Tempo no pipeline", key: d => d.age, dir: "desc"},
};
const state = {q: "", priorities: new Set(), sellers: new Set(), stages: new Set(), products: new Set(), account: "all",
               sort: CFG.defaultSort, dir: SORTS[CFG.defaultSort].dir, page: 0, open: null};

function filtered() {
  const q = norm(state.q.trim());
  const rows = DATA.filter(d =>
    (!q || norm(`${d.account ?? ""} ${d.product} ${d.id} ${d.seller}`).includes(q)) &&
    (!state.priorities.size || state.priorities.has(d.priority)) &&
    (!state.sellers.size || state.sellers.has(d.seller)) &&
    (!state.stages.size || state.stages.has(d.stage)) &&
    (!state.products.size || state.products.has(d.product)) &&
    (state.account === "all" || (state.account === "with") === !d.crm));
  const s = SORTS[state.sort], sign = state.dir === "asc" ? 1 : -1;
  // Ordenação estável: empates mantêm a ordem padrão (rank); sem tempo calculável (prospecção) vai ao fim.
  return rows.sort((a, b) => {
    const ka = s.key(a), kb = s.key(b);
    if (ka === null && kb !== null) return 1;
    if (kb === null && ka !== null) return -1;
    if (ka !== kb && ka !== null) return (ka < kb ? -1 : 1) * sign;
    return a.rank - b.rank;
  });
}
const activeFilters = () => (state.q.trim() ? 1 : 0) + state.priorities.size + state.sellers.size + state.stages.size +
  state.products.size + (state.account !== "all" ? 1 : 0);

// ---------- Toolbar ----------
function menuButton(id, label, count, extraClass = "") {
  return `<div style="position:relative"><button class="fbtn ${count ? "on" : ""}" data-menu="${id}" aria-haspopup="true" aria-expanded="false">${esc(label)}${count ? `<span class="n">${count}</span>` : ""}${icon("chevron-down", 14)}</button><div class="menu ${extraClass}" id="m-${id}" role="menu"></div></div>`;
}
function renderToolbar() {
  const tb = document.getElementById("toolbar");
  const focused = document.activeElement && document.activeElement.id === "q";
  const caret = focused ? document.activeElement.selectionStart : null;
  tb.innerHTML = `
    <label class="search">${icon("search")}<input id="q" type="search" placeholder="Buscar conta, produto ou ID" value="${esc(state.q)}" aria-label="Buscar"></label>
    ${CFG.showPriority ? menuButton("priorities", "Prioridade", state.priorities.size) : ""}
    ${CFG.showSeller ? menuButton("sellers", "Vendedor", state.sellers.size) : ""}
    ${CFG.stages.length > 1 ? menuButton("stages", "Etapa", state.stages.size) : ""}
    <div style="position:relative"><button class="fbtn ${state.products.size || state.account !== "all" ? "on" : ""}" data-menu="more" aria-haspopup="true" aria-expanded="false">${icon("sliders-horizontal", 15)}Filtros${state.products.size + (state.account !== "all" ? 1 : 0) ? `<span class="n">${state.products.size + (state.account !== "all" ? 1 : 0)}</span>` : ""}</button><div class="menu" id="m-more" role="menu"></div></div>
    <button class="clear ${activeFilters() ? "show" : ""}" id="clear">${icon("x", 14)}Limpar</button>
    <span class="spacer"></span>
    <div class="sort"><span class="lbl">Ordenar por</span><div style="position:relative"><button class="fbtn" data-menu="sort" aria-haspopup="true" aria-expanded="false" id="sortbtn">${icon("arrow-down-up", 14)}${esc(SORTS[state.sort].label)}</button><div class="menu right" id="m-sort" role="menu"></div></div></div>`;
  if (focused) { const q = document.getElementById("q"); q.focus(); q.setSelectionRange(caret, caret); }
}
function options(id) {
  if (id === "priorities") return CFG.priorities.map(p => ({set: state.priorities, value: p, color: DATA.find(d => d.priority === p)?.color}));
  if (id === "sellers") return CFG.sellers.map(s => ({set: state.sellers, value: s}));
  if (id === "stages") return CFG.stages.map(s => ({set: state.stages, value: s}));
  return [];
}
function openMenu(id, btn) {
  closeMenus();
  const m = document.getElementById("m-" + id);
  let html = "";
  if (id === "sort") {
    html = Object.entries(SORTS).map(([k, s]) => `<button class="opt ${state.sort === k ? "sel" : ""}" data-sort="${k}" role="menuitemradio" aria-checked="${state.sort === k}"><span class="box">${state.sort === k ? icon("check", 12) : ""}</span>${esc(s.label)}${k === "priority" ? ' <span class="muted">(padrão)</span>' : ""}</button>`).join("");
  } else if (id === "more") {
    html = `<h4>Produto</h4>` + CFG.products.map(p => opt(state.products, p, "products")).join("") +
      `<h4>Conta no CRM</h4>` + [["all", "Todas"], ["with", "Informada"], ["without", "Não informada"]].map(([v, l]) =>
        `<button class="opt ${state.account === v ? "sel" : ""}" data-account="${v}" role="menuitemradio" aria-checked="${state.account === v}"><span class="box">${state.account === v ? icon("check", 12) : ""}</span>${l}</button>`).join("");
  } else {
    html = options(id).map(o => opt(o.set, o.value, id, o.color)).join("");
  }
  m.innerHTML = html;
  m.classList.add("open");
  btn.setAttribute("aria-expanded", "true");
}
function opt(set, value, group, color) {
  const sel = set.has(value);
  return `<button class="opt ${sel ? "sel" : ""}" data-group="${group}" data-value="${esc(value)}" role="menuitemcheckbox" aria-checked="${sel}"><span class="box">${sel ? icon("check", 12) : ""}</span>${color ? `<span class="dot" style="background:${color}"></span>` : ""}${esc(value)}</button>`;
}
function closeMenus() {
  document.querySelectorAll(".menu.open").forEach(m => m.classList.remove("open"));
  document.querySelectorAll("[aria-expanded=true]").forEach(b => b.setAttribute("aria-expanded", "false"));
}

// ---------- Tabela ----------
const COLS = [
  ["acc", "Conta / oportunidade", null], ["stage", "Etapa", null], ["score", "Score", "score"], ["prio", "Prioridade", "priority"],
  ["product", "Produto", null], ["value", "Valor", "value"], ["age", "Dias", "age"], ["act", "Próxima ação", null], ["chev", "", null]];
function renderHeader() {
  document.getElementById("hdr").innerHTML = COLS.map(([k, label, sort]) => {
    const cls = ["c", "c-" + k, sort ? "s" : "", state.sort === sort ? "act" : "", k === "value" || k === "age" ? "r" : ""].join(" ");
    // Seta pelo significado: ↓ = maior primeiro (na prioridade, a ordem interna é invertida).
    const highFirst = sort === "priority" ? state.dir === "asc" : state.dir === "desc";
    const arrow = state.sort === sort ? (highFirst ? " ↓" : " ↑") : "";
    const aria = state.sort === sort ? (highFirst ? "descending" : "ascending") : "none";
    return `<div class="${cls}" role="columnheader" ${sort ? `data-sort="${sort}" tabindex="0" aria-sort="${aria}"` : ""}>${esc(label)}${arrow}</div>`;
  }).join("");
}
function rowHtml(d) {
  const sub = [d.id, CFG.showSeller ? d.seller : null].filter(Boolean).join(" · ");
  return `<div class="row cols ${state.open === d.id ? "cur" : ""}" role="row" tabindex="0" data-id="${esc(d.id)}">
    <div class="c c-acc acc" role="cell"><b class="${d.account ? "" : "none"}" title="${esc(d.account || "Conta não informada")}">${esc(d.account || "Conta não informada")}${d.dup ? '<span class="tag">duplicata?</span>' : ""}</b><span>${esc(sub)}</span></div>
    <div class="c c-stage muted" role="cell">${esc(d.stage)}</div>
    <div class="c c-score score" role="cell" data-tip="${esc(d.id)}"><strong class="num">${d.score}</strong><span class="meter"><i style="width:${d.score}%;background:${d.color}"></i></span></div>
    <div class="c c-prio prio" role="cell"><span class="dot" style="background:${d.color}"></span>${esc(d.priority)}<span class="val"> · ${esc(money(d.value))}</span></div>
    <div class="c c-product" role="cell" title="${esc(d.product)}">${esc(d.product)}</div>
    <div class="c c-value r num" role="cell">${esc(money(d.value))}</div>
    <div class="c c-age r num muted" role="cell">${d.age ?? "—"}</div>
    <div class="c c-act act" role="cell" title="${esc(d.action)}">${esc(d.action)}</div>
    <div class="c c-chev chev" role="cell">${icon("chevron-right", 16)}</div></div>`;
}
let current = [];
function render() {
  current = filtered();
  const total = DATA.length, n = current.length, size = CFG.pageSize;
  const pages = Math.max(1, Math.ceil(n / size));
  state.page = Math.min(state.page, pages - 1);
  document.getElementById("title").textContent = CFG.title;
  document.getElementById("count").textContent =
    (n === total ? plural(total, CFG.noun[0], CFG.noun[1]) : `${n.toLocaleString("pt-BR")} de ${plural(total, CFG.noun[0], CFG.noun[1])}`) + " · " + CFG.scope;
  renderToolbar(); renderHeader();
  const body = document.getElementById("body");
  if (!n) {
    body.innerHTML = `<div class="empty">${icon("search", 28)}<b>Nenhum deal encontrado</b>Nenhum deal corresponde à busca e aos filtros.<br><button id="clear2">Limpar filtros</button></div>`;
  } else {
    body.innerHTML = current.slice(state.page * size, (state.page + 1) * size).map(rowHtml).join("");
  }
  document.getElementById("range").textContent = n ? `${(state.page * size + 1).toLocaleString("pt-BR")}–${Math.min(n, (state.page + 1) * size).toLocaleString("pt-BR")} de ${n.toLocaleString("pt-BR")} · ordenado por ${SORTS[state.sort].label.toLowerCase()}` : "";
  document.getElementById("prev").disabled = state.page === 0;
  document.getElementById("next").disabled = state.page >= pages - 1;
}

// ---------- Tooltip do score ----------
const tip = document.getElementById("tip");
function showTip(el) {
  const d = DATA.find(x => x.id === el.dataset.tip); if (!d) return;
  tip.innerHTML = `<div class="t">${d.score} · ${esc(d.priority)}</div>
    <div class="l"><span>Valor</span><span>${d.pv} de ${CFG.weights[0]}</span></div>
    <div class="l"><span>Momento</span><span>${d.pm} de ${CFG.weights[1]}</span></div>
    <div style="margin-top:6px">${esc(d.short)}</div>`;
  const r = el.getBoundingClientRect();
  tip.style.left = Math.max(8, Math.min(r.left, innerWidth - 296)) + "px";
  const below = r.bottom + 8, h = 110;
  tip.style.top = (below + h > innerHeight ? r.top - h - 8 : below) + "px";
  tip.classList.add("show");
}
const hideTip = () => tip.classList.remove("show");

// ---------- Drawer ----------
const drawer = document.getElementById("drawer"), shade = document.getElementById("shade");
let lastFocus = null;
function openDrawer(id) {
  const d = DATA.find(x => x.id === id); if (!d) return;
  state.open = id; lastFocus = document.activeElement;
  const fact = (k, v) => `<div><dt>${k}</dt><dd title="${esc(v)}">${esc(v)}</dd></div>`;
  drawer.innerHTML = `
    <div class="dh"><div><h2 id="dtitle">${esc(d.product)} · ${esc(d.account || "Conta não informada")}</h2><p>${esc(d.id)} · ${esc(d.seller)} · ${esc(d.manager)} · ${esc(d.region)}</p></div>
      <button class="x" id="close" aria-label="Fechar">${icon("x", 16)}</button></div>
    <div class="db">
      <div class="big"><strong>${d.score}</strong><span class="prio"><span class="dot" style="background:${d.color}"></span>${esc(d.priority)}</span></div>
      <dl class="facts">${fact("Conta", d.account || "Não informada")}${fact("Produto", d.product)}${fact("Valor (preço de lista)", money(d.value))}${fact("Etapa", d.stage)}${fact("Dias em negociação", d.age ?? "Ainda não engajado")}${fact("Vendedor", d.seller)}</dl>
      <div class="sec"><h3>Recomendação</h3><div class="rec">${icon("arrow-right", 16)}<div>${esc(d.action)}</div></div></div>
      <div class="sec"><h3>Composição do score</h3>
        <div class="bar"><div class="lab"><span>Valor</span><span class="num">${d.pv} de ${CFG.weights[0]}</span></div><div class="trk"><i style="width:${d.pv / CFG.weights[0] * 100}%"></i></div></div>
        <div class="bar"><div class="lab"><span>Momento</span><span class="num">${d.pm} de ${CFG.weights[1]}</span></div><div class="trk"><i style="width:${d.pm / CFG.weights[1] * 100}%"></i></div></div></div>
      <div class="sec"><h3>Principais fatores</h3><ul class="rs">${d.reasons.map(([c, t]) => `<li><span class="dot" style="background:${c}"></span><span>${esc(t)}</span></li>`).join("")}</ul></div>
    </div>`;
  drawer.classList.add("open"); shade.classList.add("open"); drawer.setAttribute("aria-hidden", "false");
  document.querySelectorAll(".row.cur").forEach(r => r.classList.remove("cur"));
  document.querySelector(`.row[data-id="${CSS.escape(id)}"]`)?.classList.add("cur");
  document.getElementById("close").focus();
}
function closeDrawer() {
  if (!state.open) return;
  drawer.classList.remove("open"); shade.classList.remove("open"); drawer.setAttribute("aria-hidden", "true");
  const row = document.querySelector(`.row[data-id="${CSS.escape(state.open)}"]`);
  state.open = null;
  document.querySelectorAll(".row.cur").forEach(r => r.classList.remove("cur"));
  (row || lastFocus)?.focus({preventScroll: true});
}

// ---------- Eventos ----------
document.addEventListener("click", e => {
  const t = e.target.closest("button, .row, [data-sort]");
  if (!e.target.closest(".menu") && !e.target.closest("[data-menu]")) closeMenus();
  if (!t) return;
  if (t.dataset.menu) { const m = document.getElementById("m-" + t.dataset.menu); m.classList.contains("open") ? closeMenus() : openMenu(t.dataset.menu, t); return; }
  if (t.dataset.group) {
    const set = {priorities: state.priorities, sellers: state.sellers, stages: state.stages, products: state.products}[t.dataset.group];
    set.has(t.dataset.value) ? set.delete(t.dataset.value) : set.add(t.dataset.value);
    state.page = 0; const menu = t.dataset.group === "products" ? "more" : t.dataset.group; render();
    openMenu(menu, document.querySelector(`[data-menu="${menu}"]`)); return;
  }
  if (t.dataset.account) { state.account = t.dataset.account; state.page = 0; render(); openMenu("more", document.querySelector('[data-menu="more"]')); return; }
  if (t.dataset.sort) {
    const k = t.dataset.sort;
    if (t.closest(".hdr") && state.sort === k) state.dir = state.dir === "asc" ? "desc" : "asc";
    else { state.sort = k; state.dir = SORTS[k].dir; }
    state.page = 0; closeMenus(); render(); return;
  }
  if (t.id === "clear" || t.id === "clear2") {
    Object.assign(state, {q: "", account: "all", page: 0});
    [state.priorities, state.sellers, state.stages, state.products].forEach(s => s.clear()); render(); return;
  }
  if (t.id === "prev") { state.page--; render(); document.getElementById("grid").scrollTop = 0; return; }
  if (t.id === "next") { state.page++; render(); document.getElementById("grid").scrollTop = 0; return; }
  if (t.id === "close") { closeDrawer(); return; }
  if (t.classList.contains("row") && t.dataset.id) openDrawer(t.dataset.id);
});
shade.addEventListener("click", closeDrawer);
document.addEventListener("input", e => { if (e.target.id === "q") { state.q = e.target.value; state.page = 0; render(); } });
document.addEventListener("keydown", e => {
  if (e.key === "Escape") { if (state.open) closeDrawer(); else closeMenus(); hideTip(); }
  if (e.key === "Enter" && e.target.classList?.contains("row")) openDrawer(e.target.dataset.id);
  if (e.key === "Enter" && e.target.dataset?.sort && e.target.closest(".hdr")) e.target.click();
});
document.addEventListener("mouseover", e => { const s = e.target.closest("[data-tip]"); if (s) showTip(s); });
document.addEventListener("mouseout", e => { if (e.target.closest("[data-tip]") && !e.relatedTarget?.closest?.("[data-tip]")) hideTip(); });
document.getElementById("grid").addEventListener("scroll", hideTip);
document.getElementById("prev").innerHTML = icon("chevron-left");
document.getElementById("next").innerHTML = icon("chevron-right");

render();
if (CFG.initialDeal && DATA.some(d => d.id === CFG.initialDeal)) {
  const i = current.findIndex(d => d.id === CFG.initialDeal);
  if (i >= 0) { state.page = Math.floor(i / CFG.pageSize); render(); }
  openDrawer(CFG.initialDeal);
  document.querySelector(`.row[data-id="${CSS.escape(CFG.initialDeal)}"]`)?.scrollIntoView({block: "center"});
}
</script></body></html>"""
