import argparse
import json
import logging
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set, Tuple

from config import DEFAULT_TAXONOMY_PATH, get_db_config, load_env, parse_import_languages
from db_utils import connect_db


LOGGER = logging.getLogger("taxonomy.import")
LABEL_RE = re.compile(r"[^a-z0-9]+")


def split_language_from_code(code: str) -> str:
    return code.split(":", 1)[0] if ":" in code else ""


def normalize_ltree_label(code: str) -> str:
    # strip accents and combining marks, keep hyphens, replace other separators with underscore
    import unicodedata

    s = code.strip().lower()
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    # replace any non-alphanumeric (including ':' and '-') with underscore
    normalized = LABEL_RE.sub("_", s)
    # collapse multiple underscores
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "unknown"


def load_taxonomy_json(json_path: Path) -> Dict[str, Any]:
    with json_path.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_graph(
    payload: Dict[str, Any],
    import_languages: List[str],
) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, List[str]], Dict[str, Set[str]], List[str]]:
    selected = {
        code: data
        for code, data in payload.items()
        if split_language_from_code(code) in import_languages
    }

    parents_map: Dict[str, List[str]] = {}
    children_map: Dict[str, Set[str]] = defaultdict(set)

    for code, data in selected.items():
        raw_parents = data.get("parents") or []
        in_scope_parents = [parent for parent in raw_parents if parent in selected]
        parents_map[code] = in_scope_parents

        for parent in in_scope_parents:
            children_map[parent].add(code)

    roots = [code for code in selected if not parents_map.get(code)]
    return selected, parents_map, children_map, roots


def build_paths(
    selected: Dict[str, Dict[str, Any]],
    children_map: Dict[str, Set[str]],
    roots: List[str],
) -> Dict[str, Set[str]]:
    paths_by_code: Dict[str, Set[str]] = defaultdict(set)

    def dfs(code: str, path_labels: List[str], visiting: Set[str]) -> None:
        if code in visiting:
            LOGGER.warning("Cycle detected while traversing %s; skipping recursive branch", code)
            return

        current_path = [*path_labels, normalize_ltree_label(code)]
        paths_by_code[code].add(".".join(current_path))

        next_visiting = set(visiting)
        next_visiting.add(code)
        for child in sorted(children_map.get(code, set())):
            dfs(child, current_path, next_visiting)

    traversal_roots = roots[:] if roots else list(selected.keys())
    for root in traversal_roots:
        dfs(root, [], set())

    for code in selected:
        if code not in paths_by_code:
            dfs(code, [], set())

    return paths_by_code


def determine_fallback_language(name_map: Dict[str, str], import_languages: List[str]) -> str | None:
    non_empty_names = {lang: value for lang, value in name_map.items() if value}
    if not non_empty_names:
        return None

    if len(non_empty_names) == 1:
        return next(iter(non_empty_names))

    translated_by_order = [lang for lang in import_languages if lang in non_empty_names]
    if len(translated_by_order) < len(import_languages):
        if translated_by_order:
            return translated_by_order[0]
        return next(iter(non_empty_names))

    return None


def build_rows(
    selected: Dict[str, Dict[str, Any]],
    import_languages: List[str],
    paths_by_code: Dict[str, Set[str]],
) -> Tuple[List[Tuple[str, str | None]], List[Tuple[str, str]], List[Tuple[str, str, str]], List[Tuple[str, str, str]]]:
    taxonomy_rows: List[Tuple[str, str | None]] = []
    path_rows: List[Tuple[str, str]] = []
    name_rows: List[Tuple[str, str, str]] = []
    synonym_rows: List[Tuple[str, str, str]] = []

    for code, data in selected.items():
        names_map = data.get("name") or {}
        synonyms_map = data.get("synonyms") or {}

        fallback_language = determine_fallback_language(names_map, import_languages)
        taxonomy_rows.append((code, fallback_language))

        for path in sorted(paths_by_code.get(code, {normalize_ltree_label(code)})):
            path_rows.append((code, path))

        effective_languages = set(import_languages)
        if len([lang for lang, value in names_map.items() if value]) == 1:
            effective_languages.update(names_map.keys())

        code_tail = code.split(":", 1)[1] if ":" in code else code
        fallback_name = names_map.get(fallback_language, code_tail) if fallback_language else code_tail

        for language in sorted(effective_languages):
            resolved_name = names_map.get(language) or fallback_name
            name_rows.append((code, language, resolved_name))

            raw_synonyms = synonyms_map.get(language)
            if not raw_synonyms and fallback_language:
                raw_synonyms = synonyms_map.get(fallback_language)

            for synonym in sorted({item.strip() for item in (raw_synonyms or []) if item and item.strip()}):
                synonym_rows.append((code, language, synonym))

    return taxonomy_rows, path_rows, name_rows, synonym_rows


def chunked_rows(rows: Iterable[Tuple[Any, ...]], chunk_size: int = 5000) -> Iterable[List[Tuple[Any, ...]]]:
    batch: List[Tuple[Any, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) >= chunk_size:
            yield batch
            batch = []
    if batch:
        yield batch


def import_category(json_path: Path) -> None:
    env_values = load_env()
    import_languages = parse_import_languages(env_values)
    if not import_languages:
        raise ValueError("IMPORT_LANGUAGES is required and cannot be empty")

    payload = load_taxonomy_json(json_path)
    selected, _parents_map, children_map, roots = build_graph(payload, import_languages)
    paths_by_code = build_paths(selected, children_map, roots)

    taxonomy_rows, path_rows, name_rows, synonym_rows = build_rows(
        selected,
        import_languages,
        paths_by_code,
    )

    db_config = get_db_config(env_values)
    with connect_db(db_config) as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                TRUNCATE TABLE off_category_synonyms,
                               off_category_names,
                               off_category_paths,
                               off_category
                """
            )

            for batch in chunked_rows(taxonomy_rows):
                cur.executemany(
                    "INSERT INTO off_category (code, fallback_language) VALUES (%s, %s)",
                    batch,
                )

            for batch in chunked_rows(path_rows):
                cur.executemany(
                    "INSERT INTO off_category_paths (code, tree) VALUES (%s, %s::ltree)",
                    batch,
                )

            for batch in chunked_rows(name_rows):
                cur.executemany(
                    "INSERT INTO off_category_names (code, language, name) VALUES (%s, %s, %s)",
                    batch,
                )

            for batch in chunked_rows(synonym_rows):
                cur.executemany(
                    "INSERT INTO off_category_synonyms (code, language, synonym) VALUES (%s, %s, %s)",
                    batch,
                )

        conn.commit()

    LOGGER.info("Imported taxonomy codes: %s", len(taxonomy_rows))
    LOGGER.info("Imported taxonomy paths: %s", len(path_rows))
    LOGGER.info("Imported taxonomy names: %s", len(name_rows))
    LOGGER.info("Imported taxonomy synonyms: %s", len(synonym_rows))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Import off_category into PostgreSQL")
    parser.add_argument(
        "--input",
        default=str(DEFAULT_TAXONOMY_PATH),
        help="Path to taxonomy JSON file",
    )
    return parser


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    parser = build_parser()
    args = parser.parse_args()
    import_category(Path(args.input))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
