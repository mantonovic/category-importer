import argparse
import json
import logging
import re
import unicodedata
from pathlib import Path
from typing import Iterable, List, Set

from config import DEFAULT_TAXONOMY_PATH, get_db_config, load_env
from db_utils import connect_db


LOGGER = logging.getLogger("taxonomy.find")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")


def normalize_label(code: str) -> str:
    s = code.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = NON_ALNUM_RE.sub("_", s)
    s = re.sub(r"_+", "_", s).strip("_")
    return s or "unknown"


def normalize_codes(codes: Iterable[str]) -> (List[str], Set[str]):
    codes_list = [c.strip() for c in codes if c and c.strip()]
    normalized = [normalize_label(c) for c in codes_list]
    return codes_list, set(normalized)


def find_paths_for_codes(codes: List[str], json_output: bool = False):
    env = load_env()
    db_config = get_db_config(env)

    _, normalized_set = normalize_codes(codes)

    # fetch paths for given codes (each code may have multiple paths)
    found_paths = set()
    with connect_db(db_config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT code, tree::text FROM off_category_paths WHERE code = ANY(%s)",
                (codes,),
            )
            rows = cur.fetchall()

    for code, tree_text in rows:
        components = tree_text.split(".")
        if all(comp in normalized_set for comp in components):
            found_paths.add(tree_text)

    results = sorted(found_paths)

    # keep only maximal paths (exclude any path that is a strict prefix of another)
    maximal = []
    results_set = set(results)
    for p in results:
        prefix = p + "."
        is_prefix = any(other != p and other.startswith(prefix) for other in results)
        if not is_prefix:
            maximal.append(p)

    if json_output:
        print(json.dumps(maximal, ensure_ascii=False, indent=2))
    else:
        for p in maximal:
            print(p)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Find off_category_paths composed from given codes")
    parser.add_argument("codes", nargs="*", help="Codes like en:breakfasts")
    parser.add_argument("--file", help="File with one code per line")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()

    codes = list(args.codes or [])
    if args.file:
        p = Path(args.file)
        if p.exists():
            codes.extend([line.strip() for line in p.read_text(encoding="utf-8").splitlines() if line.strip()])
        else:
            LOGGER.error("File not found: %s", args.file)
            return 2

    if not codes:
        LOGGER.error("No codes provided")
        return 1

    find_paths_for_codes(codes, json_output=args.json)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
