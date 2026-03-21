import argparse
import logging
from pathlib import Path

from config import DEFAULT_SCHEMA_PATH, get_db_config, load_env
from db_utils import connect_db, execute_schema_if_needed


LOGGER = logging.getLogger("taxonomy.init_db")


def init_db(schema_path: Path) -> bool:
    env_values = load_env()
    db_config = get_db_config(env_values)
    with connect_db(db_config) as conn:
        created = execute_schema_if_needed(conn, schema_path)

    if created:
        LOGGER.info("Created missing taxonomy tables from %s", schema_path)
    else:
        LOGGER.info("All taxonomy tables already exist")

    return created


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Initialize taxonomy tables")
    parser.add_argument(
        "--schema",
        default=str(DEFAULT_SCHEMA_PATH),
        help="Path to SQL schema file",
    )
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    init_db(Path(args.schema))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
