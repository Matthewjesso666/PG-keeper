# PG-keeper

A lightweight toolkit to ingest Workers' Compensation Board case materials, chat with context, and draft responses via CLI or API.

## Features
- Ingest local files or directories into Chroma/FAISS
- Chat over indexed context and view retrieved snippets
- Draft concise notes or replies with configurable tone/length
- Optional FastAPI service exposing `/chat` and `/draft`

## Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[api]
```

## CLI Usage
```bash
pg-keeper-ingest ./case-vault
pg-keeper-chat "What deadlines are mentioned?"
pg-keeper-draft "Draft an appeal note summarizing the latest decision"
```

Set environment variables to configure behavior:
- `PG_KEEPER_DATA_DIR` to control where data is stored (default `./data`)
- `PG_KEEPER_CHROMA_URL` to point at a remote Chroma server (default in-process)
- `PG_KEEPER_API_KEY` to protect the API (optional)
- `PG_KEEPER_MODEL` to set the model name used in generated text

## API Usage
Start the API locally:
```bash
uvicorn api.app:app --reload
```

Make requests with an API key if configured:
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $PG_KEEPER_API_KEY" \
  -d '{"query": "List missing evidence", "collection": "case-vault", "top_k": 3}'

curl -X POST http://localhost:8000/draft \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Draft follow-up email to adjuster", "tone": "direct", "length": "medium"}'
```

## Docker
Build and run the API with Chroma via Docker Compose:
```bash
docker-compose up --build
```

This starts Chroma on port 8001 and the API on port 8000 with a shared `./data` volume.
