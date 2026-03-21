import argparse
import logging
from pathlib import Path

from config import DEFAULT_SCHEMA_PATH, DEFAULT_TAXONOMY_PATH, DEFAULT_TAXONOMY_URL
from fetch_category import fetch_category
from import_category import import_category
from init_db import init_db


LOGGER = logging.getLogger("taxonomy.orchestrator")


def run_all(url: str, output: Path, schema: Path) -> None:
    fetch_category(url, output)
    init_db(schema)
    import_category(output)
    LOGGER.info("Taxonomy import pipeline completed")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Open Food Facts taxonomy importer orchestration"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_all_parser = subparsers.add_parser("run-all", help="Run full pipeline")
    run_all_parser.add_argument("--url", default=DEFAULT_TAXONOMY_URL)
    run_all_parser.add_argument("--output", default=str(DEFAULT_TAXONOMY_PATH))
    run_all_parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))

    fetch_parser = subparsers.add_parser("fetch", help="Download taxonomy JSON")
    fetch_parser.add_argument("--url", default=DEFAULT_TAXONOMY_URL)
    fetch_parser.add_argument("--output", default=str(DEFAULT_TAXONOMY_PATH))

    init_parser = subparsers.add_parser("init-db", help="Create schema if needed")
    init_parser.add_argument("--schema", default=str(DEFAULT_SCHEMA_PATH))

    import_parser = subparsers.add_parser("import", help="Load taxonomy data into PostgreSQL")
    import_parser.add_argument("--input", default=str(DEFAULT_TAXONOMY_PATH))

    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run-all":
        run_all(args.url, Path(args.output), Path(args.schema))
    elif args.command == "fetch":
        fetch_category(args.url, Path(args.output))
    elif args.command == "init-db":
        init_db(Path(args.schema))
    elif args.command == "import":
        import_category(Path(args.input))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
