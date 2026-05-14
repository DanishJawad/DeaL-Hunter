# Deal Hunter

Deal Hunter is a neon-dark game price finder that answers two things well:
exact game pricing and similar-game discovery.

It uses local Ollama for AI reasoning, CheapShark for live prices, and Pinecone for semantic search.

## Screenshots

Replace these placeholders with your final images when you’re ready:

![Home screen placeholder](docs/screenshots/home.png)
![Exact game pricing placeholder](docs/screenshots/exact-game-pricing.png)
![Similar games placeholder](docs/screenshots/similar-games.png)

## What It Does

- Finds the cheapest current price for a specific game.
- Shows all available store prices and direct links.
- Finds similar games when the user asks for recommendations.
- Uses alias matching for titles like GTA V, GTA 5, and Grand Theft Auto V.
- Keeps AI reasoning local and free with Ollama.

## How It Works

```text
User types a query in Streamlit
  -> app checks whether it is an exact game query
  -> exact game: fetch all CheapShark deals for that title
  -> discovery query: use Pinecone to find similar games
  -> rank results and build explanations
  -> show best deal first with store links
```

## Project Structure

```text
.
├── app/                # application code
├── assets/             # brand assets like the logo
├── data/               # game CSVs and cache files
├── docs/               # project guide and screenshots
├── scripts/            # dataset and Pinecone setup scripts
├── main.py             # Streamlit entry point
├── README.md           # this guide
├── pyproject.toml      # project metadata
├── requirements.txt    # dependency list
└── .streamlit/         # Streamlit config
```

## Main Files

| File | Purpose |
| --- | --- |
| `main.py` | Launches the Streamlit app. |
| `app/ui.py` | Builds the full user interface. |
| `app/agent.py` | Coordinates exact-game and discovery flows. |
| `app/cheapshark.py` | Talks to CheapShark and returns live deals. |
| `app/vectorstore.py` | Handles Pinecone semantic search. |
| `app/games_db.py` | Loads the game catalog and resolves aliases. |
| `app/preferences.py` | Stores session preferences and parses the query. |
| `app/deal_logic.py` | Scores deals and builds explanations. |
| `app/models.py` | Pydantic models for games, deals, and recommendations. |

## Setup

1. Install Ollama: https://ollama.ai
2. Pull models:
   ```bash
   ollama pull mistral
   ollama pull nomic-embed-text
   ```
3. Start Ollama:
   ```bash
   ollama serve
   ```
4. Create and sync the environment:
   ```bash
   uv venv
   source .venv/bin/activate
   uv sync
   ```
5. Copy `.env.example` to `.env`.
6. Set `PINECONE_API_KEY` and, optionally, `CHEAPSHARK_USER_AGENT`.

## Build the Data

```bash
python scripts/build_games_database.py
python scripts/generate_game_embeddings.py
python scripts/pinecone_setup.py
```

## Run the App

```bash
streamlit run main.py
```

## Example Queries

- Where can I get GTA V the cheapest?
- Games like Baldur's Gate 3 under $30
- Best story-driven games on sale
- Fast-paced shooters under $20

## Notes

- The vector database improves discovery, not the size of the catalog.
- For a direct title query, Deal Hunter now shows one game only.
- For similar-game queries, it shows the best matching games and current prices.

## License

MIT
