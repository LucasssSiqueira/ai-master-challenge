"""Motivos e ação recomendada em português, por template (determinístico e auditável)."""
import math
from typing import Any

POSITIVE, NEUTRAL, NEGATIVE, INFO = "✅", "➖", "⚠️", "ℹ️"


def money(value: float) -> str:
    return f"US$ {value:,.0f}".replace(",", ".")


def _first_name(full_name: str) -> str:
    return full_name.split()[0]


def value_reason(row: Any, stats: Any) -> tuple[str, str]:
    # Posição do preço na escala log do catálogo (0 = mais barato, 1 = mais caro).
    lo, hi = math.log(stats.min_price), math.log(stats.max_price)
    share = (math.log(row.sales_price) - lo) / (hi - lo)
    detail = f"{row.product} ({money(row.sales_price)}), {_price_rank(row.sales_price, stats)}"
    if share >= 0.65:
        return POSITIVE, f"Valor alto: {detail}."
    if share >= 0.35:
        return NEUTRAL, f"Valor médio: {detail}."
    return NEGATIVE, f"Valor baixo: {detail}."


def _price_rank(price: float, stats: Any) -> str:
    """Posição real do preço no catálogo, em vez de um rótulo vago como "entre os mais caros"."""
    prices = stats.catalog_prices
    n, pos = len(prices), prices.index(float(price)) + 1
    if pos == 1:
        return f"o mais caro dos {n} produtos"
    if pos == n:
        return f"o mais barato dos {n} produtos"
    return f"o {pos}º mais caro dos {n} produtos"


def timing_reason(row: Any, stats: Any) -> tuple[str, str]:
    seg = row.timing_segment
    if seg == "not_engaged":
        return NEUTRAL, "Ainda em prospecção: sem data de engajamento, o momento não entra no score."
    days = int(row.age_days)
    window = f"{stats.won_p25:.0f}–{stats.won_p75:.0f} dias"
    if seg == "stale":
        return NEGATIVE, (
            f"Parado há {days} dias: nenhum deal do histórico levou mais de {stats.stale_days} dias para fechar."
        )
    if seg == "early":
        return NEUTRAL, (
            f"Engajado há {days} dias, fase inicial: metade dos deals perdidos cai nos primeiros "
            f"{stats.lost_median:.0f} dias."
        )
    if seg == "window":
        return POSITIVE, f"Dia {days} de engajamento: dentro da janela em que deals ganhos costumam fechar ({window})."
    if seg == "late":
        return NEGATIVE, (
            f"Dia {days}: passou da janela típica ({window}); 95% dos ganhos fecham até {stats.won_p95:.0f} dias."
        )
    return NEGATIVE, (
        f"Dia {days}: perto do maior ciclo já visto ({stats.stale_days} dias), com risco de virar deal parado."
    )


def prob_reason(row: Any, stats: Any) -> tuple[str, str]:
    rate, base = row.win_rate, stats.base_win_rate
    pct, base_pct = f"{rate:.0%}", f"{base:.0%}"
    if row.n_closed == 0:
        return NEUTRAL, f"Chance estimada de {base_pct}, a média do time: {_first_name(row.sales_agent)} nunca fechou {row.product}."
    basis = f"com base em {row.n_closed} deals fechados de {_first_name(row.sales_agent)} com {row.product}"
    if abs(rate - base) < 0.02:
        return NEUTRAL, f"Chance estimada de {pct}, na média do time ({base_pct}), {basis}."
    if rate > base:
        return POSITIVE, f"Chance estimada de {pct}, acima da média do time ({base_pct}), {basis}."
    return NEGATIVE, f"Chance estimada de {pct}, abaixo da média do time ({base_pct}), {basis}."


_POLARITY_ORDER = {POSITIVE: 0, NEUTRAL: 1, NEGATIVE: 2, INFO: 3}

# O porquê completo está na aba "Como o score funciona"; aqui basta o aviso.
PROB_NOT_SCORED = "Informativo: não entra no score (veja *Como o score funciona*)."


def reasons(row: Any, stats: Any, cfg: Any) -> list[str]:
    """Motivos do score, os que mais ajudam primeiro; informações sem peso no fim."""
    prob = prob_reason(row, stats)
    if cfg.weight_prob == 0:
        prob = (INFO, f"{prob[1]} {PROB_NOT_SCORED}")
    items = [value_reason(row, stats), timing_reason(row, stats), prob]
    if not row.has_account:
        items.append((NEGATIVE, "Conta não informada no CRM: sem setor e porte do cliente para análise."))
    if row.possible_duplicate:
        items.append((NEGATIVE, "Possível duplicata: há outro deal com mesmo vendedor, produto, conta e data "
                                "de engajamento. Confirme no CRM antes de trabalhar os dois."))
    items.sort(key=lambda item: _POLARITY_ORDER[item[0]])
    return [f"{icon} {text}" for icon, text in items]


def action(row: Any, stats: Any) -> str:
    band, seg = row.band, row.timing_segment
    if band == "Requalificar":
        return (
            "Confirme com o cliente se o deal ainda está vivo. Sem próximo passo marcado, "
            "encerre como perdido e libere seu tempo."
        )
    if band == "Qualificar":
        return "Qualifique: confirme necessidade e decisor e marque a primeira reunião."
    if band == "Baixa":
        return "Baixo valor ou fora do momento: trate em lote, com follow-up padrão."
    if seg in ("late", "very_late"):
        return "Acelere: o deal está saindo da janela típica. Combine uma data de decisão com o cliente."
    if seg == "early":
        return "Garanta o próximo passo nesta semana: é a fase em que mais deals se perdem."
    if band == "Alta":
        return "Foque esta semana: proponha o fechamento ou um próximo passo concreto."
    return "Mantenha a cadência: um follow-up nesta semana."
