import argparse
from pathlib import Path
from typing import Dict

from drafting import ALLOWED_TONES, DraftInputs, TemplateGenerator


def _parse_key_value_pairs(pairs: list[str]) -> Dict[str, str]:
    parsed: Dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise argparse.ArgumentTypeError(f"Fields must be provided as key=value. Got: {pair}")
        key, value = pair.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate correspondence drafts from templates.")
    parser.add_argument("--template", required=True, help="Template name (e.g. appeal_letter, evidence_request).")
    parser.add_argument("--fact", action="append", default=[], help="Add a fact to include (can be repeated).")
    parser.add_argument("--insight", action="append", default=[], help="Add an analyzer insight (can be repeated).")
    parser.add_argument("--tone", default="neutral", choices=sorted(ALLOWED_TONES), help="Tone to apply to the draft.")
    parser.add_argument("--field", action="append", default=[], help="Template field as key=value (can be repeated).")
    parser.add_argument("--output", type=Path, required=True, help="Output path for the generated draft.")
    parser.add_argument("--format", choices=["txt", "eml", "docx"], default="txt", help="Export format.")
    parser.add_argument(
        "--templates-dir",
        type=Path,
        default=Path(__file__).resolve().parents[1] / "templates",
        help="Directory containing Jinja2 templates.",
    )
    parser.add_argument("--subject", help="Optional subject line for exports that support it.")
    parser.add_argument("--from-address", dest="from_address", help="Optional sender address for .eml export.")
    parser.add_argument("--to-address", dest="to_address", help="Optional recipient address for .eml export.")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    metadata = _parse_key_value_pairs(args.field)
    for optional in ("subject", "from_address", "to_address"):
        value = getattr(args, optional)
        if value:
            metadata[optional if optional != "subject" else "subject"] = value

    generator = TemplateGenerator(args.templates_dir)
    inputs = DraftInputs(
        facts=args.fact,
        insights=args.insight,
        metadata=metadata,
        tone=args.tone,
    )
    rendered = generator.generate(args.template, inputs)
    generator.export(rendered, args.output, fmt=args.format, metadata=metadata)
    print(f"Draft saved to {args.output} ({args.format}).")


if __name__ == "__main__":
    main()
