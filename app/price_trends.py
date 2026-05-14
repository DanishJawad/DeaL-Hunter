from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PriceTrend:
    historical_low: float | None
    typical_discount: float | None
    trend: str
    advice: str


def analyze_price_trends(game_title: str, history_path: Path) -> PriceTrend:
    if not history_path.exists():
        return PriceTrend(None, None, "Unknown", "No history available")

    title_key = game_title.strip().lower()
    with history_path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if (row.get("title") or "").strip().lower() != title_key:
                continue
            historical_low = _to_optional_float(row.get("historical_low"))
            typical_discount = _to_optional_float(row.get("typical_discount"))
            last_price = _to_optional_float(row.get("last_price"))
            previous_price = _to_optional_float(row.get("previous_price"))

            trend = "Stable"
            if last_price is not None and previous_price is not None:
                if last_price < previous_price:
                    trend = "Falling"
                elif last_price > previous_price:
                    trend = "Rising"

            advice = "Wait for seasonal sale"
            if trend == "Falling":
                advice = "Good timing, buy now"
            elif trend == "Rising":
                advice = "Price increasing, buy soon"

            return PriceTrend(historical_low, typical_discount, trend, advice)

    return PriceTrend(None, None, "Unknown", "No history available")


def _to_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
