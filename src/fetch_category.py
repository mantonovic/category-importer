import argparse
import logging
from pathlib import Path
from urllib.request import urlretrieve

from config import DEFAULT_TAXONOMY_PATH, DEFAULT_TAXONOMY_URL


LOGGER = logging.getLogger("taxonomy.fetch")


def fetch_category(url: str, destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    LOGGER.info("Downloading off_category from %s", url)
    urlretrieve(url, destination)
    LOGGER.info("Saved off_category to %s", destination)
    return destination


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fetch Open Food Facts off_category JSON")
    parser.add_argument("--url", default=DEFAULT_TAXONOMY_URL, help="Source taxonomy URL")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_TAXONOMY_PATH),
        help="Destination JSON file path",
    )
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    fetch_category(args.url, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
