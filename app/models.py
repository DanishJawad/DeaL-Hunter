from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class UserIntent(BaseModel):
    model_config = ConfigDict(extra="ignore")

    query: str
    max_price: float = 20.0
    genres: list[str] = Field(default_factory=list)
    sort_by: str = "deal_score"


class Game(BaseModel):
    model_config = ConfigDict(extra="ignore")

    game_id: str | None = None
    title: str
    genres: list[str] = Field(default_factory=list)
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    aliases: list[str] = Field(default_factory=list)
    typical_price: float | None = None
    metacritic_score: float | None = None
    steam_rating: float | None = None


class Deal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    deal_id: str
    store_id: str
    title: str
    sale_price: float
    normal_price: float
    deal_rating: float
    metacritic_score: float | None = None
    steam_rating_percent: float | None = None
    thumb: str | None = None
    steam_app_id: str | None = None


class MatchedDeal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    game: Game
    deal: Deal
    title_score: float


class RankedDeal(BaseModel):
    model_config = ConfigDict(extra="ignore")

    game: Game
    deal: Deal
    deal_score: float
    reasoning: str
    store_name: str | None = None
    relevance_score: float | None = None
    discount_percent: float | None = None


class DealEvaluation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    score: float
    verdict: str
    reason: str


class PriceTrendInfo(BaseModel):
    model_config = ConfigDict(extra="ignore")

    historical_low: float | None = None
    typical_discount: float | None = None
    trend: str | None = None
    advice: str | None = None


class Recommendation(BaseModel):
    model_config = ConfigDict(extra="ignore")

    game: Game
    deal: Deal
    store_name: str | None = None
    discount_percent: float | None = None
    deal_evaluation: DealEvaluation | None = None
    reasoning: str | None = None
    price_trend: PriceTrendInfo | None = None


class ToolResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str
    payload: Any
