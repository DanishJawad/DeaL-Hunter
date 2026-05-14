from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_ollama import ChatOllama
from pydantic import BaseModel, Field

from .cheapshark import CheapSharkClient
from .deal_logic import build_recommendation, personalize_recommendations
from .error_handler import PineconeError
from .games_db import (
    GameLookup,
    find_game_by_name,
    find_game_in_query,
    normalize_title,
    search_by_keyword,
    suggest_similar_titles,
)
from .models import Game, Recommendation
from .prompts import AGENT_SYSTEM_PROMPT
from .vectorstore import PineconeStore

LOGGER = logging.getLogger(__name__)


class SearchDealsInput(BaseModel):
    query: str = Field(..., description="User query for deal search")
    max_price: float = Field(..., description="Max price for deals")


class FindSimilarGamesInput(BaseModel):
    query: str = Field(..., description="Game title or query")
    limit: int = Field(5, description="Number of similar games to return")


class AliasInput(BaseModel):
    game_name: str = Field(..., description="Game title or alias")


class DealQualityInput(BaseModel):
    game_title: str = Field(..., description="Game title")
    current_price: float = Field(..., description="Current price")
    original_price: float = Field(..., description="Original price")
    store: str = Field(..., description="Store name")
    deal_rating: float = Field(..., description="CheapShark deal rating")


@dataclass(frozen=True)
class DealResults:
    recommendations: list[Recommendation]
    suggestions: list[str]
    is_exact_game: bool = False


def build_llm(model: str, base_url: str) -> ChatOllama:
    return ChatOllama(model=model, base_url=base_url, temperature=0.2)


def build_tools(
    cheapshark: CheapSharkClient,
    store: PineconeStore | None,
    lookup: GameLookup,
    store_map: dict[str, str],
) -> list[Any]:
    @tool("search_cheapshark_deals", args_schema=SearchDealsInput)
    def search_cheapshark_deals(query: str, max_price: float) -> list[dict[str, Any]]:
        """Find current deals from CheapShark."""
        deals = cheapshark.fetch_deals(query=query, max_price=max_price)
        return [deal.model_dump() for deal in deals]

    @tool("search_game_database", args_schema=FindSimilarGamesInput)
    def search_game_database(query: str, limit: int = 5) -> list[dict[str, Any]]:
        """Search Pinecone for similar games and return game metadata."""
        if store is None:
            games = search_by_keyword(query, lookup, limit=limit)
        else:
            try:
                games = store.search_similar_games(query=query, top_k=limit)
            except PineconeError:
                games = search_by_keyword(query, lookup, limit=limit)
        return [game.model_dump() for game in games]

    @tool("find_game_by_alias", args_schema=AliasInput)
    def find_game_by_alias(game_name: str) -> dict[str, Any] | None:
        """Return an exact match for a known game alias if available."""
        match = find_game_by_name(game_name, lookup)
        return match.model_dump() if match else None

    @tool("evaluate_deal_quality", args_schema=DealQualityInput)
    def evaluate_deal_quality_tool(
        game_title: str,
        current_price: float,
        original_price: float,
        store: str,
        deal_rating: float,
    ) -> dict[str, Any]:
        """Evaluate deal quality and return a score with reasoning."""
        from .deal_logic import evaluate_deal_quality

        evaluation = evaluate_deal_quality(
            game_title=game_title,
            current_price=current_price,
            original_price=original_price,
            store=store,
            deal_rating=deal_rating,
        )
        return evaluation.model_dump()

    @tool("get_game_details")
    def get_game_details(game_title: str) -> dict[str, Any]:
        """Combine Pinecone metadata and CheapShark deals for a game title."""
        games = search_game_database(game_title, limit=1)
        deals = search_cheapshark_deals(game_title, max_price=60)
        store_name = None
        if deals:
            store_id = str(deals[0].get("store_id"))
            store_name = store_map.get(store_id)
        return {
            "game": games[0] if games else None,
            "deals": deals,
            "store_name": store_name,
        }

    return [
        search_cheapshark_deals,
        search_game_database,
        find_game_by_alias,
        evaluate_deal_quality_tool,
        get_game_details,
    ]


def build_agent_executor(llm: ChatOllama, tools: list[Any]) -> ChatOllama:
    """Return the LLM for simple reasoning without full agent executor."""
    return llm


def run_deal_agent_sync(user_query: str, executor: ChatOllama) -> str:
    """Generate agent reasoning using the LLM."""
    prompt = ChatPromptTemplate.from_messages([("system", AGENT_SYSTEM_PROMPT)])
    chain = prompt | executor
    try:
        result = chain.invoke({"user_query": user_query})
        return str(result.content if hasattr(result, "content") else result).strip()
    except Exception as exc:
        logging.warning("Agent reasoning failed", extra={"error": str(exc)})
        return "Unable to generate reasoning at this time."


def _needs_recommendations(query: str) -> bool:
    lowered = query.lower()
    triggers = ["like", "similar", "recommend", "recommendation", "games", "titles"]
    return any(token in lowered for token in triggers)


def get_recommendations(
    *,
    query: str,
    max_price: float,
    lookup: GameLookup,
    cheapshark: CheapSharkClient,
    store: PineconeStore | None,
    store_map: dict[str, str],
    price_history_path,
    favorite_genres: list[str],
    limit: int = 5,
    search_fn: Callable[[str, int], list[dict]] | None = None,
) -> DealResults:
    alias_match = find_game_by_name(query, lookup) or find_game_in_query(query, lookup)
    recommend_mode = _needs_recommendations(query)
    is_exact_game = alias_match is not None and not recommend_mode

    if is_exact_game:
        deals = cheapshark.fetch_deals(query=alias_match.title, max_price=None)
        target_norm = normalize_title(alias_match.title)
        filtered_deals = [
            deal for deal in deals if target_norm and target_norm in normalize_title(deal.title)
        ]
        if filtered_deals:
            deals = filtered_deals
        if not deals:
            suggestions = suggest_similar_titles(query, lookup)
            return DealResults(recommendations=[], suggestions=suggestions, is_exact_game=True)

        recommendations: list[Recommendation] = []
        for deal in deals:
            store_name = store_map.get(deal.store_id)
            recommendations.append(
                build_recommendation(
                    game=alias_match,
                    deal=deal,
                    store_name=store_name,
                    price_history_path=price_history_path,
                )
            )
        return DealResults(recommendations=recommendations, suggestions=[], is_exact_game=True)

    games: list[Game] = []
    if alias_match and not recommend_mode:
        games = [alias_match]
    else:
        if store is None:
            games = search_by_keyword(query, lookup, limit=limit)
        else:
            try:
                if search_fn:
                    games = [Game.model_validate(item) for item in search_fn(query, limit)]
                else:
                    games = store.search_similar_games(
                        query=alias_match.title if alias_match else query,
                        top_k=limit,
                    )
            except PineconeError:
                games = search_by_keyword(query, lookup, limit=limit)

    suggestions: list[str] = []
    if not games:
        suggestions = suggest_similar_titles(query, lookup)
        return DealResults(recommendations=[], suggestions=suggestions)

    recommendations: list[Recommendation] = []
    for game in games:
        deals = cheapshark.fetch_deals(query=game.title, max_price=max_price)
        if not deals:
            continue
        best_deal = max(deals, key=lambda item: item.deal_rating)
        store_name = store_map.get(best_deal.store_id)
        recommendations.append(
            build_recommendation(
                game=game,
                deal=best_deal,
                store_name=store_name,
                price_history_path=price_history_path,
            )
        )

    if not recommendations:
        fallback_deals = cheapshark.fetch_deals(query=query, max_price=max_price)
        for deal in fallback_deals[:limit]:
            fallback_game = Game(title=deal.title)
            store_name = store_map.get(deal.store_id)
            recommendations.append(
                build_recommendation(
                    game=fallback_game,
                    deal=deal,
                    store_name=store_name,
                    price_history_path=price_history_path,
                )
            )

    recommendations = personalize_recommendations(recommendations, favorite_genres)
    return DealResults(recommendations=recommendations, suggestions=suggestions, is_exact_game=False)
