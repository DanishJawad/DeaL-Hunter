from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
from pinecone import Pinecone, ServerlessSpec

from app.config import load_config
from app.ollama_helper import embed_text, init_ollama


def init_pinecone(api_key: str) -> Pinecone:
    return Pinecone(api_key=api_key)


def create_game_index(client: Pinecone, name: str, dimension: int, cloud: str, region: str):
    index_names = client.list_indexes()
    if hasattr(index_names, "names"):
        existing = list(index_names.names())
    elif isinstance(index_names, dict) and "indexes" in index_names:
        existing = [item.get("name", "") for item in index_names["indexes"]]
    else:
        existing = []

    if name not in existing:
        client.create_index(
            name=name,
            dimension=dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud=cloud, region=region),
        )
    return client.Index(name)


def embed_and_upsert_games(games_df: pd.DataFrame, index, batch_size: int = 100) -> None:
    vectors = []
    for _, row in games_df.iterrows():
        embedding = row.get("embedding")
        if isinstance(embedding, str):
            embedding = json.loads(embedding)
        if not isinstance(embedding, list):
            continue
        game_id = str(row.get("game_id"))
        metadata = {
            "title": row.get("title"),
            "genres": str(row.get("genres", "")).split(","),
            "description": row.get("description"),
            "tags": str(row.get("tags", "")).split(","),
            "aliases": str(row.get("aliases", "")).split(","),
            "typical_price": row.get("typical_price"),
            "metacritic_score": row.get("metacritic_avg"),
        }
        vectors.append((game_id, embedding, metadata))
        if len(vectors) >= batch_size:
            index.upsert(vectors=vectors)
            vectors = []

    if vectors:
        index.upsert(vectors=vectors)


def search_similar_games(index, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    vector = embed_text(query)
    results = index.query(vector=vector, top_k=top_k, include_metadata=True)
    return results.get("matches") or []


def main() -> None:
    config = load_config()
    init_ollama()

    client = init_pinecone(config.pinecone_api_key)
    index = create_game_index(
        client,
        config.pinecone_index_name,
        config.ollama_embed_dim,
        config.pinecone_cloud,
        config.pinecone_region,
    )

    embeddings_path = Path(config.games_embeddings_path)
    if not embeddings_path.exists():
        raise SystemExit(
            f"Missing embeddings at {embeddings_path}. Run generate_game_embeddings.py first."
        )

    games_df = pd.read_csv(embeddings_path)
    embed_and_upsert_games(games_df, index)
    print("Upsert complete")

    matches = search_similar_games(index, "Games like GTA V", top_k=3)
    for match in matches:
        print(match.get("metadata", {}).get("title"))


if __name__ == "__main__":
    main()
