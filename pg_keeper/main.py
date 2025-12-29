"""Command-line interface for PG-keeper."""
from __future__ import annotations

import argparse
import logging
from pathlib import Path

from pg_keeper.config import AgentConfig, CaseVaultConfig, GoogleAuthConfig
from pg_keeper.llm import EchoLLMClient, OpenAILLMClient
from pg_keeper.pipeline import CaseAgent

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")


def build_agent(args: argparse.Namespace) -> CaseAgent:
    google_auth = None
    if args.google_credentials:
        google_auth = GoogleAuthConfig(Path(args.google_credentials))
    case_vault = None
    if args.case_vault:
        case_vault = CaseVaultConfig(Path(args.case_vault))
    llm_client = EchoLLMClient() if args.offline else OpenAILLMClient(model=args.model)

    config = AgentConfig(
        google=google_auth,
        case_vault=case_vault,
        llm_model=args.model,
        response_recipient=args.recipient,
        dry_run=args.dry_run,
    )
    return CaseAgent(config=config, llm_client=llm_client, google_auth=google_auth, case_vault=case_vault)


def main() -> None:
    parser = argparse.ArgumentParser(description="PG-keeper case agent")
    parser.add_argument("--case-vault", help="Path to the case vault folder")
    parser.add_argument("--google-credentials", help="Path to Google OAuth credentials file")
    parser.add_argument("--model", default="openai/gpt-4.1-mini", help="LLM model identifier")
    parser.add_argument("--recipient", default="Claims Manager", help="Who receives drafted responses")
    parser.add_argument("--offline", action="store_true", help="Use offline echo model for testing")
    parser.add_argument("--dry-run", action="store_true", help="Skip sending messages")
    args = parser.parse_args()

    agent = build_agent(args)
    draft = agent.run()
    print("Subject:", draft.subject)
    print("\n" + draft.body)


if __name__ == "__main__":
    main()
