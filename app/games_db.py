from __future__ import annotations

import csv
from dataclasses import dataclass
from difflib import get_close_matches
from pathlib import Path

from .error_handler import GameDataError
from .models import Game


@dataclass(frozen=True)
class GameLookup:
    games: list[Game]
    alias_map: dict[str, Game]


def _normalize(text: str) -> str:
    return "".join(ch for ch in text.lower().strip() if ch.isalnum())


def _split_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def load_games_database(path: Path) -> GameLookup:
    if not path.exists():
        try:
            from .games_dataset import build_games_database

            build_games_database(path)
        except Exception as exc:  # pragma: no cover - depends on runtime
            raise GameDataError(f"Missing games database at {path}") from exc

    games: list[Game] = []
    alias_map: dict[str, Game] = {}

    with path.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            title = (row.get("title") or "").strip()
            if not title:
                continue
            game = Game(
                game_id=(row.get("game_id") or "").strip(),
                title=title,
                genres=_split_list(row.get("genres")),
                description=(row.get("description") or "").strip() or None,
                tags=_split_list(row.get("tags")),
                aliases=_split_list(row.get("aliases")),
                typical_price=_to_optional_float(row.get("typical_price")),
                metacritic_score=_to_optional_float(row.get("metacritic_avg")),
            )
            games.append(game)
            for alias in {title, *game.aliases}:
                alias_map[_normalize(alias)] = game

    return GameLookup(games=games, alias_map=alias_map)


def find_game_by_name(query: str, lookup: GameLookup) -> Game | None:
    normalized = _normalize(query)
    if not normalized:
        return None
    return lookup.alias_map.get(normalized)


def normalize_title(text: str) -> str:
    return _normalize(text)


def find_game_in_query(query: str, lookup: GameLookup) -> Game | None:
    normalized_query = _normalize(query)
    if not normalized_query:
        return None

    best_match = None
    best_length = 0
    for alias, game in lookup.alias_map.items():
        if alias and alias in normalized_query and len(alias) > best_length:
            best_match = game
            best_length = len(alias)

    return best_match


def search_by_keyword(query: str, lookup: GameLookup, limit: int = 5) -> list[Game]:
    token = query.strip().lower()
    if not token:
        return []
    results = []
    for game in lookup.games:
        haystack = " ".join(
            [game.title, " ".join(game.aliases), " ".join(game.genres), " ".join(game.tags)]
        ).lower()
        if token in haystack:
            results.append(game)
        if len(results) >= limit:
            break
    return results


def suggest_similar_titles(query: str, lookup: GameLookup, limit: int = 5) -> list[str]:
    titles = [game.title for game in lookup.games]
    return get_close_matches(query, titles, n=limit, cutoff=0.6)


def _to_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
