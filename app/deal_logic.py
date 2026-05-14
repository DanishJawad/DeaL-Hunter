from __future__ import annotations

from typing import Iterable

from .models import Deal, DealEvaluation, Game, PriceTrendInfo, Recommendation
from .price_trends import analyze_price_trends


_STORE_TRUST = {
    "steam": 1.0,
    "epic": 1.0,
    "epic games store": 1.0,
    "gog": 1.0,
    "humble": 1.0,
    "greenmangaming": 1.1,
    "fanatical": 1.1,
}


def discount_percent(normal_price: float, sale_price: float) -> float:
    if normal_price <= 0:
        return 0.0
    return max(0.0, min(100.0, (normal_price - sale_price) / normal_price * 100.0))


def evaluate_deal_quality(
    *,
    game_title: str,
    current_price: float,
    original_price: float,
    store: str,
    deal_rating: float,
) -> DealEvaluation:
    discount = discount_percent(original_price, current_price)
    trust = _STORE_TRUST.get(store.lower(), 1.2)
    score = (discount / 100.0) * max(1.0, deal_rating) / trust
    score = max(0.0, min(10.0, score))

    if discount >= 60:
        verdict = "Buy immediately"
        reason = "Huge discount"
    elif discount >= 35:
        verdict = "Good deal"
        reason = "Strong discount"
    else:
        verdict = "Wait for better deal"
        reason = "Discount is modest"

    return DealEvaluation(score=score, verdict=verdict, reason=reason)


def explain_deal(
    *,
    game_title: str,
    current_price: float,
    original_price: float,
    store: str,
    deal_rating: float,
    price_trend: PriceTrendInfo | None = None,
) -> str:
    discount = discount_percent(original_price, current_price)
    trust_label = "Trusted" if store.lower() in _STORE_TRUST and _STORE_TRUST[store.lower()] <= 1.0 else "Less common"

    timing = "Good deal"
    if discount >= 60:
        timing = "Best price"
    elif discount <= 20:
        timing = "Wait for sale"

    trend_line = ""
    if price_trend and price_trend.advice:
        trend_line = f"\n- 🕒 {price_trend.advice}"

    return (
        f"- 💸 {discount:.0f}% off ({current_price:.2f} from {original_price:.2f})\n"
        f"- 🏪 {trust_label} store: {store}\n"
        f"- ⭐ Deal rating: {deal_rating:.1f}\n"
        f"- ✅ {timing}{trend_line}"
    )


def build_recommendation(
    *,
    game: Game,
    deal: Deal,
    store_name: str | None,
    price_history_path,
) -> Recommendation:
    trend = analyze_price_trends(game.title, price_history_path)
    trend_info = PriceTrendInfo(
        historical_low=trend.historical_low,
        typical_discount=trend.typical_discount,
        trend=trend.trend,
        advice=trend.advice,
    )
    evaluation = evaluate_deal_quality(
        game_title=game.title,
        current_price=deal.sale_price,
        original_price=deal.normal_price,
        store=store_name or "unknown",
        deal_rating=deal.deal_rating,
    )
    reasoning = explain_deal(
        game_title=game.title,
        current_price=deal.sale_price,
        original_price=deal.normal_price,
        store=store_name or "unknown",
        deal_rating=deal.deal_rating,
        price_trend=trend_info,
    )
    return Recommendation(
        game=game.model_dump(),
        deal=deal.model_dump(),
        store_name=store_name,
        discount_percent=discount_percent(deal.normal_price, deal.sale_price),
        deal_evaluation=evaluation,
        reasoning=reasoning,
        price_trend=trend_info.model_dump(),
    )


def personalize_recommendations(
    recommendations: Iterable[Recommendation],
    favorite_genres: list[str],
) -> list[Recommendation]:
    if not favorite_genres:
        return list(recommendations)
    favorites = {genre.lower() for genre in favorite_genres}

    def _score(rec: Recommendation) -> tuple[int, float]:
        matches = len({genre.lower() for genre in rec.game.genres} & favorites)
        base = rec.deal_evaluation.score if rec.deal_evaluation else 0.0
        return (matches, base)

    return sorted(recommendations, key=_score, reverse=True)
