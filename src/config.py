import os
from pathlib import Path
from typing import Dict, List


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ENV_PATH = PROJECT_ROOT / ".env"
DEFAULT_DATA_DIR = PROJECT_ROOT / "data"
DEFAULT_TAXONOMY_URL = "https://static.openfoodfacts.org/data/taxonomies/categories.full.json"
DEFAULT_TAXONOMY_PATH = DEFAULT_DATA_DIR / "categories.full.json"
DEFAULT_SCHEMA_PATH = PROJECT_ROOT / "db" / "1-DB-SCHEMA.sql"


def load_env(env_path: Path = DEFAULT_ENV_PATH) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if env_path.exists():
        for raw_line in env_path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")

    for key, value in os.environ.items():
        values[key] = value

    return values


def parse_import_languages(env_values: Dict[str, str]) -> List[str]:
    raw = env_values.get("IMPORT_LANGUAGES", "")
    return [lang.strip() for lang in raw.split(",") if lang.strip()]


def get_db_config(env_values: Dict[str, str]) -> Dict[str, str]:
    required_keys = [
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
        "POSTGRES_DB",
        "POSTGRES_HOST",
        "POSTGRES_PORT",
    ]

    missing = [key for key in required_keys if not env_values.get(key)]
    if missing:
        raise ValueError(f"Missing database env vars: {', '.join(missing)}")

    return {
        "user": env_values["POSTGRES_USER"],
        "password": env_values["POSTGRES_PASSWORD"],
        "dbname": env_values["POSTGRES_DB"],
        "host": env_values["POSTGRES_HOST"],
        "port": env_values["POSTGRES_PORT"],
    }
