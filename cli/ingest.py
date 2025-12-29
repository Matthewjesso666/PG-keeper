import argparse

from pipelines.ingest import IngestPipeline


def parse_args():
    parser = argparse.ArgumentParser(description="Incremental ingestion for WCB case data.")
    parser.add_argument("--config", default="config/settings.yaml", help="Path to settings YAML.")
    parser.add_argument(
        "--watch",
        action="store_true",
        help="Run continuously on the configured schedule instead of once.",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    pipeline = IngestPipeline(config_path=args.config)
    if args.watch:
        pipeline.run_forever()
    else:
        new_records = pipeline.run_once()
        print(f"Ingested {len(new_records)} new documents.")


if __name__ == "__main__":
    main()
