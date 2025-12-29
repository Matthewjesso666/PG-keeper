# WCB Agent

This project scaffolds an AI assistant to help manage a Workers’ Compensation Board (WCB) case. The agent can ingest emails and files, index them, delegate analysis to specialized modules, and expose workflows over an API.

## Prerequisites
- Python 3.10+
- Git

## Quickstart
1. **Clone** this repository and navigate into it.
2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .\\.venv\\Scripts\\activate
   ```
3. **Upgrade pip and install dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r wcb-agent/requirements.txt
   ```
4. **Create a `.env` file** at the repository root to hold secrets (see `.env.example` for required keys). You can generate a local secret with:
   ```bash
   python -c "import secrets; print(secrets.token_hex(16))"
   ```
5. **Run the API**
   ```bash
   uvicorn app.main:app --reload --app-dir wcb-agent
   ```

## Environment configuration
All configuration lives in `.env`. At minimum, provide:
- `OPENAI_API_KEY`
- `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` (OAuth client credentials)
- `GOOGLE_REFRESH_TOKEN` (authorized for Gmail and Drive scopes)
- `CASE_VAULT_PATH` (local folder containing PDFs/scans)

## Project layout
- `app/main.py` – FastAPI entrypoint exposing health and data refresh endpoints.
- `app/config.py` – Centralized settings via `pydantic`.
- `app/services/` – Connectors for Gmail, Drive, and local vault ingestion.
- `app/indexing/` – Utilities for building searchable vector indexes from ingested content.
- `app/agents/` – Specialized GPT modules (Loophole Finder, Fairness Review Expert, Appeal Strategist, Dirty Tactics Defender, Case Memory/Vault).
- `app/routers/` – API routers for case management.

## Development notes
- Keep secrets in `.env` (never commit this file).
- Extend the specialized agents in `app/agents/analysis.py` to add prompts, retrieval strategies, or chain logic.
- The Gmail/Drive connectors assume OAuth2 with a stored refresh token; replace credential handling as needed for your workflow.
