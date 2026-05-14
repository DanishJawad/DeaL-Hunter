from __future__ import annotations

from pathlib import Path

from app.games_dataset import build_games_database


def main() -> None:
    output_path = Path(__file__).resolve().parents[1] / "data" / "games_database.csv"
    build_games_database(output_path)
    print(f"Wrote games database to {output_path}")


if __name__ == "__main__":
    main()
