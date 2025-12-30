"""CLI helpers for enforcing profile-based safety policies."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Dict, Tuple

from pg_keeper.audit.logging import AuditLogger, AuditRecord
from pg_keeper.safety.filters import SafetyPolicyError, evaluate_policy_and_redact


DEFAULT_CONFIG = Path(__file__).resolve().parent.parent / "config" / "profiles.yaml"


def _load_config_text(path: Path) -> Dict:
    text = path.read_text()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Fallback for environments where PyYAML is unavailable. The configuration
        # is authored in JSON-compatible YAML, so a lightweight parser keeps the
        # dependency surface small.
        try:
            import yaml  # type: ignore

            return yaml.safe_load(text)
        except Exception as exc:  # pragma: no cover - defensive fallback
            raise RuntimeError(f"Unable to parse configuration at {path}: {exc}") from exc


def load_profiles(config_path: Path | None = None) -> Dict[str, Dict]:
    path = Path(config_path) if config_path else DEFAULT_CONFIG
    data = _load_config_text(path) or {}
    return data.get("profiles", {})


def get_profile(name: str, config_path: Path | None = None) -> Dict:
    profiles = load_profiles(config_path)
    if name not in profiles:
        available = ", ".join(sorted(profiles)) or "<none>"
        raise KeyError(f"Unknown profile '{name}'. Available profiles: {available}")
    return profiles[name]


def send_draft(
    profile_name: str,
    content: str,
    *,
    config_path: Path | None = None,
    source_id: str = "cli",
    audit_logger: AuditLogger | None = None,
    redaction_override: bool | None = None,
) -> Tuple[str, AuditRecord, AuditLogger]:
    settings = get_profile(profile_name, config_path)
    logger = audit_logger or AuditLogger()

    sanitized = evaluate_policy_and_redact(content, settings, redaction_override=redaction_override)

    record = logger.log_action(
        action="send_draft",
        input_data={"profile": profile_name, "content": content},
        output_data={"profile": profile_name, "content": sanitized},
        source_id=source_id,
    )
    return sanitized, record, logger


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PG Keeper CLI")
    parser.add_argument("profile", help="Profile to use for safety enforcement")
    parser.add_argument("content", help="Draft content to send")
    parser.add_argument(
        "--source-id",
        default="cli",
        help="Identifier for the source initiating the action",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG,
        help="Path to profiles configuration",
    )
    parser.add_argument(
        "--no-redact",
        dest="redact",
        action="store_false",
        help="Disable redaction even if the profile requires it",
    )
    parser.set_defaults(redact=None)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        sanitized, record, _ = send_draft(
            args.profile,
            args.content,
            config_path=args.config,
            source_id=args.source_id,
            redaction_override=args.redact,
        )
    except SafetyPolicyError as exc:  # pragma: no cover - exercised in integration test
        parser.error(str(exc))
        return 1

    print(sanitized)
    print(f"logged at {record.timestamp.isoformat()} from {record.source_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
