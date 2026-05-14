from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.ollama_helper import embed_text, init_ollama


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    input_path = root / "data" / "games_database.csv"
    output_path = root / "data" / "games_with_embeddings.csv"

    if not input_path.exists():
        raise SystemExit(f"Missing games database at {input_path}. Run build_games_database.py first.")

    init_ollama()

    games_df = pd.read_csv(input_path)
    cached_embeddings: dict[str, list[float]] = {}

    if output_path.exists():
        existing_df = pd.read_csv(output_path)
        for _, row in existing_df.iterrows():
            game_id = str(row.get("game_id"))
            embedding_raw = row.get("embedding")
            if game_id and isinstance(embedding_raw, str):
                try:
                    cached_embeddings[game_id] = json.loads(embedding_raw)
                except json.JSONDecodeError:
                    continue

    embeddings = []
    total = len(games_df)
    for idx, row in games_df.iterrows():
        game_id = str(row.get("game_id"))
        description = str(row.get("description", ""))
        genres = str(row.get("genres", ""))
        tags = str(row.get("tags", ""))
        text = " ".join([description, genres, tags]).strip()

        if game_id in cached_embeddings:
            vector = cached_embeddings[game_id]
        else:
            vector = embed_text(text)

        embeddings.append(json.dumps(vector))
        print(f"Embedding game {idx + 1}/{total}...")

    games_df["embedding"] = embeddings
    games_df.to_csv(output_path, index=False)
    print(f"Saved embeddings to {output_path}")


if __name__ == "__main__":
    main()
