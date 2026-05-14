from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Iterable

from pinecone import Pinecone, ServerlessSpec

from .config import AppConfig
from .error_handler import GameDataError, PineconeError
from .models import Game
from .ollama_helper import embed_text

LOGGER = logging.getLogger(__name__)


class PineconeStore:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        if not config.pinecone_api_key:
            raise PineconeError("Missing Pinecone API key")
        self.client = Pinecone(api_key=config.pinecone_api_key)
        self.index = self._ensure_index()

    def _ensure_index(self):
        index_name = self.config.pinecone_index_name
        dimension = self.config.ollama_embed_dim
        index_names = self._list_index_names()

        if index_name not in index_names:
            LOGGER.info("Creating Pinecone index", extra={"index": index_name, "dimension": dimension})
            self.client.create_index(
                name=index_name,
                dimension=dimension,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud=self.config.pinecone_cloud,
                    region=self.config.pinecone_region,
                ),
            )
        return self.client.Index(index_name)

    def _list_index_names(self) -> list[str]:
        index_list = self.client.list_indexes()
        if hasattr(index_list, "names"):
            return list(index_list.names())
        if isinstance(index_list, dict) and "indexes" in index_list:
            return [item.get("name", "") for item in index_list["indexes"]]
        if isinstance(index_list, list):
            return [item.get("name", "") if isinstance(item, dict) else str(item) for item in index_list]
        return []

    def get_vector_count(self) -> int:
        try:
            stats = self.index.describe_index_stats()
        except Exception as exc:
            raise PineconeError("Failed to read Pinecone stats") from exc
        count = stats.get("total_vector_count")
        return int(count) if count is not None else 0

    def ensure_games_indexed(self, embeddings_path: Path, min_count: int = 150) -> int:
        current_count = self.get_vector_count()
        if current_count >= min_count:
            return current_count
        self.upsert_games_from_embeddings(embeddings_path)
        return self.get_vector_count()

    def upsert_games_from_embeddings(self, embeddings_path: Path, batch_size: int = 100) -> None:
        if not embeddings_path.exists():
            raise GameDataError(f"Missing embeddings file at {embeddings_path}")

        vectors = []
        with embeddings_path.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                embedding = _parse_embedding(row.get("embedding"))
                if not embedding:
                    continue
                game_id = (row.get("game_id") or row.get("id") or row.get("title") or "").strip()
                if not game_id:
                    continue
                metadata = {
                    "title": (row.get("title") or "").strip(),
                    "genres": _split_list(row.get("genres")),
                    "description": (row.get("description") or "").strip(),
                    "tags": _split_list(row.get("tags")),
                    "aliases": _split_list(row.get("aliases")),
                    "typical_price": _to_optional_float(row.get("typical_price")),
                    "metacritic_score": _to_optional_float(row.get("metacritic_avg")),
                }
                vectors.append((game_id, embedding, metadata))

                if len(vectors) >= batch_size:
                    self.index.upsert(vectors=vectors)
                    vectors = []

        if vectors:
            self.index.upsert(vectors=vectors)

    def search_similar_games(
        self,
        query: str,
        top_k: int = 5,
        genres: list[str] | None = None,
    ) -> list[Game]:
        vector = embed_text(query)
        filters = None
        if genres:
            filters = {"genres": {"$in": genres}}
        try:
            results = self.index.query(
                vector=vector,
                top_k=top_k,
                include_metadata=True,
                filter=filters,
            )
        except Exception as exc:
            raise PineconeError("Pinecone query failed") from exc

        matches = results.get("matches") or []
        games: list[Game] = []
        for match in matches:
            metadata = match.get("metadata") or {}
            games.append(
                Game(
                    game_id=match.get("id"),
                    title=metadata.get("title") or "",
                    genres=list(metadata.get("genres") or []),
                    description=metadata.get("description"),
                    tags=list(metadata.get("tags") or []),
                    aliases=list(metadata.get("aliases") or []),
                    typical_price=metadata.get("typical_price"),
                    metacritic_score=metadata.get("metacritic_score"),
                )
            )
        return games


def _parse_embedding(raw: str | None) -> list[float]:
    if not raw:
        return []
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    return [float(value) for value in payload]


def _split_list(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip() for item in raw.split(",") if item.strip()]


def _to_optional_float(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
