from __future__ import annotations

import re
from dataclasses import dataclass


_PRICE_PATTERNS = [
    re.compile(r"\$\s*(\d+(?:\.\d+)?)"),
    re.compile(r"(\d+(?:\.\d+)?)\s*(?:usd|dollars|bucks)"),
    re.compile(r"(?:under|below|less than|up to|max(?:imum)?|no more than)\s*\$?\s*(\d+(?:\.\d+)?)"),
]

_GENRE_ALIASES = {
    "action": "Action",
    "adventure": "Adventure",
    "casual": "Casual",
    "indie": "Indie",
    "rpg": "RPG",
    "role-playing": "RPG",
    "roleplaying": "RPG",
    "roguelike": "RPG",
    "rogue-like": "RPG",
    "racing": "Racing",
    "simulation": "Simulation",
    "sim": "Simulation",
    "sports": "Sports",
    "strategy": "Strategy",
    "horror": "Horror",
    "puzzle": "Puzzle",
    "shooter": "Shooter",
    "fps": "Shooter",
}


@dataclass(frozen=True)
class ParsedIntent:
    max_price: float
    genres: list[str]
    notes: list[str]
    used_parser: bool


def parse_intent(
    query: str,
    available_genres: list[str],
    default_max_price: float,
    default_genres: list[str],
) -> ParsedIntent:
    text = query.strip().lower()
    matched_prices: list[float] = []

    for pattern in _PRICE_PATTERNS:
        for match in pattern.findall(text):
            try:
                matched_prices.append(float(match))
            except ValueError:
                continue

    max_price = default_max_price
    notes: list[str] = []
    used_parser = False

    if matched_prices:
        max_price = max(1.0, min(matched_prices))
        notes.append(f"Max price ${max_price:.0f}")
        used_parser = True

    available_set = {genre.lower(): genre for genre in available_genres}
    found_genres: list[str] = []

    for token, canonical in _GENRE_ALIASES.items():
        if token in text:
            resolved = available_set.get(canonical.lower(), canonical)
            if resolved in available_genres and resolved not in found_genres:
                found_genres.append(resolved)

    for genre in available_genres:
        if genre.lower() in text and genre not in found_genres:
            found_genres.append(genre)

    if found_genres:
        notes.append("Genres: " + ", ".join(found_genres))
        used_parser = True

    merged_genres = default_genres
    if found_genres:
        merged_genres = sorted({*default_genres, *found_genres})

    return ParsedIntent(
        max_price=max_price,
        genres=merged_genres,
        notes=notes,
        used_parser=used_parser,
    )


def extract_price_limit(query: str) -> float | None:
    text = query.strip().lower()
    matched_prices: list[float] = []
    for pattern in _PRICE_PATTERNS:
        for match in pattern.findall(text):
            try:
                matched_prices.append(float(match))
            except ValueError:
                continue
    if not matched_prices:
        return None
    return max(1.0, min(matched_prices))
