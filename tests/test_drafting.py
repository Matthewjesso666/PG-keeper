from pathlib import Path

import pytest

from drafting.generator import DraftInputs, MissingFieldsError, TemplateGenerator


TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates"


def test_missing_required_fields_for_appeal_letter():
    generator = TemplateGenerator(TEMPLATES_DIR)
    inputs = DraftInputs(
        metadata={
            "case_id": "WCB-12345",
            "requested_action": "Reinstate benefits effective immediately.",
        },
        tone="neutral",
    )

    with pytest.raises(MissingFieldsError) as excinfo:
        generator.generate("appeal_letter", inputs)

    missing_fields = set(excinfo.value.missing_fields)
    assert {"claimant_name", "signature"} <= missing_fields


def test_renders_appeal_letter_with_tone_and_details():
    generator = TemplateGenerator(TEMPLATES_DIR)
    inputs = DraftInputs(
        facts=["The injury occurred while performing assigned duties."],
        insights=["Policy provisions on modified duties were not considered."],
        metadata={
            "case_id": "WCB-12345",
            "claimant_name": "Jordan Smith",
            "requested_action": "Reconsider and approve wage-loss benefits.",
            "recipient_name": "Case Manager",
            "signature": "Jordan Smith",
        },
        tone="firm",
    )

    rendered = generator.generate("appeal_letter", inputs)

    assert "Jordan Smith" in rendered
    assert "WCB-12345" in rendered
    assert "prompt and complete attention" in rendered  # tone phrase
    assert "Policy provisions on modified duties were not considered." in rendered
    assert "The injury occurred while performing assigned duties." in rendered


def test_invalid_tone_is_rejected():
    generator = TemplateGenerator(TEMPLATES_DIR)
    inputs = DraftInputs(
        metadata={
            "case_id": "WCB-67890",
            "documents_requested": ["Complete claim file", "Medical assessments"],
            "context_summary": "Need to verify the evidence relied upon for the last decision.",
            "signature": "Jordan Smith",
        },
        tone="urgent",
    )

    with pytest.raises(ValueError):
        generator.generate("evidence_request", inputs)
