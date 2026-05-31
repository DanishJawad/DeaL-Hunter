from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Callable

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
import json
import re
import time
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
from .nlp import extract_price_limit
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


def build_agent_executor(llm: ChatOllama, tools: list[Any]) -> Callable[[str], str]:
    """Return a simple tool-calling executor.

    This executor uses the provided `llm` to decide whether to call one of the
    provided `tools` (by name) or to return a final answer. It expects the LLM
    to emit a JSON object when it wants to call a tool, for example:
    {"action": "search_game_database", "args": {"query": "GTA V", "limit": 3}}

    The executor will call the named tool and append the tool result back into
    the conversation for the LLM to consume in the next step. This is a simple
    loop-based agent (not the full LangChain agent factory) that works reliably
    with the local Ollama chat model used in this project.
    """

    # Build a name -> callable mapping for tools
    tool_map: dict[str, Callable] = {}
    for t in tools:
        name = getattr(t, "name", None) or getattr(t, "__name__", None)
        if name:
            tool_map[name] = t

    system_instructions = (
        AGENT_SYSTEM_PROMPT
        + "\n\nTool protocol:\n"
        + "If you want to call a tool, reply with a JSON object ONLY, for example:\n"
        + "{\"action\": \"search_game_database\", \"args\": {\"query\": \"GTA V\", \"limit\": 3}}\n"
        + "When you are finished and have the final user-facing answer, reply with:\n"
        + "{\"final\": \"Your final answer text here\"}\n"
        + "Do not output any extra text outside the JSON object."
    )

    def executor(user_query: str) -> str:
        messages = [("system", system_instructions), ("user", user_query)]

        last_content = ""
        # allow a few tool-call cycles
        for _ in range(4):
            try:
                resp = llm.invoke(messages)
            except Exception as exc:  # pragma: no cover - runtime errors
                return f"Agent LLM error: {exc}"

            content = getattr(resp, "content", str(resp)) or ""
            last_content = content.strip()

            # Try to extract a JSON object from the LLM reply
            json_obj = None
            try:
                m = re.search(r"\{.*\}", content, re.S)
                if m:
                    json_text = m.group(0)
                    json_obj = json.loads(json_text)
            except Exception:
                json_obj = None

            if not json_obj:
                # No JSON -> treat as final human text
                return last_content

            if "final" in json_obj:
                return str(json_obj["final"]).strip()

            action = json_obj.get("action")
            args = json_obj.get("args", {}) or {}
            if not action:
                messages.append(("system", "Invalid tool call: missing 'action' key."))
                continue

            tool_fn = tool_map.get(action)
            if not tool_fn:
                messages.append(("system", f"Tool not found: {action}"))
                continue

            # Call the tool and stringify the result for the LLM
            try:
                tool_result = tool_fn(**args)
                # Convert pydantic / model objects to serializable forms
                if isinstance(tool_result, list):
                    serializable = []
                    for item in tool_result:
                        if hasattr(item, "model_dump"):
                            serializable.append(item.model_dump())
                        elif hasattr(item, "dict"):
                            serializable.append(item.dict())
                        else:
                            serializable.append(item)
                else:
                    if hasattr(tool_result, "model_dump"):
                        serializable = tool_result.model_dump()
                    elif hasattr(tool_result, "dict"):
                        serializable = tool_result.dict()
                    else:
                        serializable = tool_result
                tool_json = json.dumps(serializable, default=str)
            except Exception as exc:  # pragma: no cover - defensive
                tool_json = json.dumps({"error": str(exc)})

            # Append tool result for the LLM to consume on the next turn
            messages.append(("system", f"TOOL_RESULT:{action}:{tool_json}"))
            # small pause to avoid hammering local Ollama in tight loops
            time.sleep(0.05)

        # If we run out of cycles, return the last content
        return last_content

    return executor


def run_deal_agent_sync(user_query: str, executor: ChatOllama | Callable[[str], str]) -> str:
    """Generate agent reasoning using the provided executor.

    If `executor` is a callable (the simple tool-calling executor returned by
    `build_agent_executor`) we call it directly. If `executor` is an LLM/chat
    model (e.g. `ChatOllama`) we fall back to the previous prompt chaining
    behaviour.
    """
    # If executor is a plain callable (our loop-based agent), call it directly
    if callable(executor) and not hasattr(executor, "invoke"):
        try:
            return executor(user_query)
        except Exception as exc:
            logging.warning("Agent executor failed", extra={"error": str(exc)})
            return "Unable to generate reasoning at this time."

    # Otherwise, assume it's a chat model compatible with prompt chaining
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
    price_limit = extract_price_limit(query)
    effective_max_price = price_limit if price_limit is not None else max_price

    if is_exact_game:
        deals = cheapshark.fetch_deals(query=alias_match.title, max_price=price_limit)
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
        deals = cheapshark.fetch_deals(query=game.title, max_price=effective_max_price)
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
        fallback_deals = cheapshark.fetch_deals(query=query, max_price=effective_max_price)
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
