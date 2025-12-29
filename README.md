# PG-keeper

A Python agent that keeps a Workers' Compensation Board (WCB) case organized by
pulling correspondence and files, indexing them, delegating analysis to
specialized GPT modules, and drafting responses.

## Features
- Sync adapters for Gmail, Google Drive, and a local **case vault** folder (PDF, TXT, MD).
- Keyword-based categorization and indexing for fast triage.
- Specialist analyzers (Loophole Finder, Fairness Review, Appeal Strategist,
  Dirty Tactics Defender, Case Memory/Vault) powered by an LLM abstraction.
- Response drafter that rolls up recommended actions for the claims manager.
- Offline-friendly defaults using an echo LLM stub; OpenAI client available when
  credentials are configured.

## Quickstart
1. Create a virtual environment and install optional dependencies if you plan to
   talk to Google or OpenAI APIs:
   ```bash
   pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib openai PyPDF2
   ```
2. Run the agent in offline mode (no external API calls) against a local vault:
   ```bash
   python -m pg_keeper.main --case-vault /path/to/case_vault --offline --dry-run
   ```
3. To enable Gmail/Drive collection, supply your OAuth credentials JSON:
   ```bash
   python -m pg_keeper.main --google-credentials credentials.json --case-vault /path/to/case_vault --dry-run
   ```

## Tests
Run the test suite with:
```bash
pytest
```

## Project Structure
- `pg_keeper/config.py` – configuration dataclasses for Google auth and vaults.
- `pg_keeper/data_sources/` – connectors for Gmail, Drive, and local vault files.
- `pg_keeper/indexer.py` – keyword-based classifier and indexer.
- `pg_keeper/analysis/specialists.py` – specialized GPT roles built on the LLM abstraction.
- `pg_keeper/pipeline.py` – orchestrates ingestion, analysis, and drafting.
- `pg_keeper/main.py` – CLI entry point.

## Notes
- External imports are lazy to keep the package importable without Google or OpenAI installed.
- The agent defaults to `dry_run` to avoid sending or filing anything; wire your own
  outbound channel if you want to deliver drafted responses automatically.
