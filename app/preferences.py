from __future__ import annotations

import json

import streamlit as st
from pydantic import BaseModel, ConfigDict, Field

from .nlp import parse_intent
from .ollama_helper import generate_text


class GamePreferences(BaseModel):
    model_config = ConfigDict(extra="ignore")

    favorite_genres: list[str] = Field(default_factory=list)
    budget: float = 30.0
    play_style: str = ""


def get_preferences() -> GamePreferences:
    raw = st.session_state.get("preferences")
    if isinstance(raw, dict):
        return GamePreferences.model_validate(raw)
    if isinstance(raw, GamePreferences):
        return raw
    return GamePreferences()


def save_preferences(preferences: GamePreferences) -> None:
    st.session_state["preferences"] = preferences.model_dump()


def extract_preferences_from_query(
    query: str,
    available_genres: list[str] | None = None,
    default_budget: float = 30.0,
    default_genres: list[str] | None = None,
) -> GamePreferences:
    prompt = (
        "Extract user preferences from the query and respond with JSON only. "
        "Fields: favorite_genres (list of strings), budget (number), play_style (string).\n"
        f"Query: {query}"
    )
    default_genres = default_genres or []
    default_prefs = GamePreferences()
    try:
        response = generate_text(prompt, temperature=0.2)
        payload = json.loads(response)
        prefs = GamePreferences.model_validate(payload)
    except (json.JSONDecodeError, ValueError):
        prefs = GamePreferences()

    if available_genres:
        parsed = parse_intent(query, available_genres, default_budget, default_genres)
        if parsed.used_parser:
            if parsed.genres:
                prefs.favorite_genres = sorted({*prefs.favorite_genres, *parsed.genres})
            if parsed.max_price and prefs.budget == default_prefs.budget:
                prefs.budget = parsed.max_price
    return prefs


def merge_preferences(current: GamePreferences, incoming: GamePreferences) -> GamePreferences:
    genres = list({*current.favorite_genres, *incoming.favorite_genres})
    budget = incoming.budget or current.budget
    play_style = incoming.play_style or current.play_style
    return GamePreferences(favorite_genres=genres, budget=budget, play_style=play_style)
