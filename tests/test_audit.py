from datetime import datetime, timezone
from pathlib import Path

from pg_keeper.audit.logging import AuditLogger
from pg_keeper.cli import DEFAULT_CONFIG, send_draft


def test_audit_logger_records_action():
    fixed_time = datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc)
    logger = AuditLogger(clock=lambda: fixed_time)

    record = logger.log_action(
        "ingest",
        input_data={"source": "email"},
        output_data={"status": "ok"},
        source_id="collector",
    )

    assert record.timestamp == fixed_time
    assert record.to_dict()["timestamp"].startswith("2024-01-01T12:00:00+00:00")
    assert logger.latest() == record


def test_send_draft_enforces_profile_and_logs(tmp_path: Path):
    config_path = Path(DEFAULT_CONFIG)
    assert config_path.exists(), "Expected config/profiles.yaml to be present"

    draft = "Email me at claimant@example.com"
    sanitized, record, logger = send_draft(
        "default",
        draft,
        config_path=config_path,
        source_id="cli-test",
    )

    assert "[REDACTED EMAIL]" in sanitized
    assert record.source_id == "cli-test"
    assert logger.latest() == record
