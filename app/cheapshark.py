from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from .cache import load_cached_json, save_cached_json
from .error_handler import CheapSharkError, retry_with_backoff
from .models import Deal, Game

LOGGER = logging.getLogger(__name__)


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


@dataclass
class CheapSharkClient:
    base_url: str
    timeout_seconds: int
    cache_dir: Path
    games_cache_ttl_seconds: int
    stores_cache_ttl_seconds: int
    user_agent: str
    _last_request_time: float = 0.0

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
        self._rate_limit()

        def _request() -> Any:
            headers = {"User-Agent": self.user_agent} if self.user_agent else None
            response = requests.get(url, params=params, timeout=self.timeout_seconds, headers=headers)
            response.raise_for_status()
            return response.json()

        try:
            return retry_with_backoff(
                _request,
                exceptions=(requests.RequestException,),
                max_retries=3,
                base_delay=0.5,
            )
        except requests.RequestException as exc:
            LOGGER.error("CheapShark request failed", extra={"url": url, "error": str(exc)})
            raise CheapSharkError("CheapShark request failed") from exc

    def _rate_limit(self) -> None:
        elapsed = time.time() - self._last_request_time
        if elapsed < 0.5:
            time.sleep(0.5 - elapsed)
        self._last_request_time = time.time()

    def fetch_deals(
        self,
        query: str | None,
        max_price: float | None,
        page_size: int = 60,
        page_number: int = 0,
        sort_by: str = "Deal Rating",
    ) -> list[Deal]:
        params: dict[str, Any] = {
            "pageSize": page_size,
            "pageNumber": page_number,
            "sortBy": sort_by,
        }
        if query:
            params["title"] = query
        if max_price is not None:
            params["upperPrice"] = max_price
        payload = self._get("deals", params=params)
        return [self._parse_deal(item) for item in payload]

    def get_game_deals(
        self,
        query: str,
        max_price: int = 50,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        deals = self.fetch_deals(query=query, max_price=max_price)
        deals = deals[:limit]
        store_map = self.fetch_stores()
        results: list[dict[str, Any]] = []
        for deal in deals:
            results.append(
                {
                    "title": deal.title,
                    "store": store_map.get(deal.store_id, deal.store_id),
                    "price": deal.sale_price,
                    "original_price": deal.normal_price,
                    "metacritic": deal.metacritic_score,
                    "steamrating": deal.steam_rating_percent,
                    "deal_rating": deal.deal_rating,
                }
            )
        return results

    def fetch_games_page(
        self,
        page_number: int,
        page_size: int,
        sort_by: str = "Metacritic",
        search_title: str | None = None,
    ) -> list[Game]:
        # Only use /games for title search, not for catalog listing
        if search_title:
            params = {"title": search_title}
            payload = self._get("games", params=params)
            if not isinstance(payload, list):
                return []
            games: list[Game] = []
            for item in payload:
                title = item.get("external") or item.get("title")
                if not title:
                    continue
                games.append(
                    Game(
                        title=title,
                        genres=[],
                        metacritic_score=_to_optional_float(item.get("metacriticScore")),
                        steam_rating=None,
                        typical_price=_to_optional_float(item.get("cheapest")),
                        description=None,
                    )
                )
            return games
        # For catalog, fallback to deals
        return self.fetch_games_from_deals(max_pages=page_number+1, page_size=page_size)

    def fetch_games_catalog(
        self,
        max_pages: int = 10,
        page_size: int = 60,
        sort_by: str = "Metacritic",
    ) -> list[Game]:
        # Use deals for catalog, not /games
        return self.fetch_games_from_deals(max_pages=max_pages, page_size=page_size)

    def fetch_games_from_deals(self, max_pages: int = 5, page_size: int = 60) -> list[Game]:
        games: list[Game] = []
        seen: set[str] = set()
        for page in range(max_pages):
            deals = self.fetch_deals(query=None, max_price=None, page_size=page_size, page_number=page)
            if not deals:
                break
            for deal in deals:
                normalized = deal.title.strip().lower()
                if normalized in seen:
                    continue
                seen.add(normalized)
                games.append(
                    Game(
                        title=deal.title,
                        genres=[],
                        metacritic_score=deal.metacritic_score,
                        steam_rating=deal.steam_rating_percent,
                        typical_price=deal.normal_price,
                        description=None,
                    )
                )
        return games

    def get_games_catalog(self, max_pages: int = 10, page_size: int = 60) -> list[Game]:
        cache_path = self.cache_dir / "games.json"
        is_fresh, cached = load_cached_json(cache_path, self.games_cache_ttl_seconds)
        if is_fresh and isinstance(cached, list):
            return [Game.model_validate(item) for item in cached]

        games = self.fetch_games_catalog(max_pages=max_pages, page_size=page_size)
        if not games:
            LOGGER.warning("CheapShark games endpoint returned no data; falling back to deals")
            games = self.fetch_games_from_deals(max_pages=max_pages)

        save_cached_json(cache_path, [game.model_dump() for game in games])
        return games

    def fetch_stores(self) -> dict[str, str]:
        cache_path = self.cache_dir / "stores.json"
        is_fresh, cached = load_cached_json(cache_path, self.stores_cache_ttl_seconds)
        if is_fresh and isinstance(cached, dict):
            return {str(k): str(v) for k, v in cached.items()}

        payload = self._get("stores")
        stores: dict[str, str] = {}
        if isinstance(payload, list):
            for item in payload:
                store_id = str(item.get("storeID"))
                store_name = str(item.get("storeName"))
                is_active = str(item.get("isActive")) == "1"
                if store_id and store_name and is_active:
                    stores[store_id] = store_name

        if stores:
            save_cached_json(cache_path, stores)
        return stores

    @staticmethod
    def _parse_deal(item: dict[str, Any]) -> Deal:
        return Deal(
            deal_id=str(item.get("dealID", "")),
            store_id=str(item.get("storeID", "")),
            title=str(item.get("title", "")),
            sale_price=_to_float(item.get("salePrice")),
            normal_price=_to_float(item.get("normalPrice")),
            deal_rating=_to_float(item.get("dealRating")),
            metacritic_score=_to_optional_float(item.get("metacriticScore")),
            steam_rating_percent=_to_optional_float(item.get("steamRatingPercent")),
            thumb=item.get("thumb"),
            steam_app_id=item.get("steamAppID"),
        )
