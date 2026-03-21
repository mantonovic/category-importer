from pathlib import Path
from typing import Any, Dict


def connect_db(db_config: Dict[str, str]) -> Any:
    import psycopg

    return psycopg.connect(
        user=db_config["user"],
        password=db_config["password"],
        dbname=db_config["dbname"],
        host=db_config["host"],
        port=db_config["port"],
    )


def execute_schema_if_needed(conn: Any, schema_path: Path) -> bool:
    required_tables = [
        "off_category",
        "off_category_paths",
        "off_category_names",
        "off_category_synonyms",
    ]

    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = ANY(%s)
            """,
            (required_tables,),
        )
        existing = {row[0] for row in cur.fetchall()}

    if existing == set(required_tables):
        return False

    schema_sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(schema_sql)
    conn.commit()
    return True
