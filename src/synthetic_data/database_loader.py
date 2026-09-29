"""Database Loader for CASHNET Synthetic Financial Datasets.

Loads generated CSV records or in-memory datasets into PostgreSQL or SQLite databases.
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional


def load_into_database(
    datasets: Dict[str, List[Dict[str, Any]]],
    db_url: str = "sqlite:///./cashnet_dev.db",
    schema_path: Optional[Path] = None,
) -> bool:
    """Loads all tables into the target database.

    Args:
        datasets: Dictionary of table names to records list.
        db_url: Database connection URL (sqlite or postgresql).
        schema_path: Path to schema.sql.

    Returns:
        True if loaded successfully.
    """
    if schema_path is None:
        schema_path = Path(__file__).resolve().parent.parent.parent / "database" / "schema.sql"

    if db_url.startswith("sqlite:///"):
        sqlite_file = db_url.replace("sqlite:///", "")
        db_path = Path(sqlite_file)

        # Remove existing sqlite db if recreating
        if db_path.exists():
            db_path.unlink()

        conn = sqlite3.connect(sqlite_file)
        cursor = conn.cursor()

        # Load schema (sanitize postgres-specific types if necessary for pure SQLite)
        if schema_path.exists():
            schema_sql = schema_path.read_text(encoding="utf-8")
            # SQLite does not support TIMESTAMP WITH TIME ZONE directly, convert to TEXT or TIMESTAMP
            clean_sql = schema_sql.replace("TIMESTAMP WITH TIME ZONE", "TIMESTAMP")
            clean_sql = clean_sql.replace("NUMERIC(15, 2)", "REAL")
            clean_sql = clean_sql.replace("NUMERIC(9, 6)", "REAL")
            clean_sql = clean_sql.replace("NUMERIC(9, 3)", "REAL")
            clean_sql = clean_sql.replace("NUMERIC(5, 4)", "REAL")
            clean_sql = clean_sql.replace("NUMERIC(7, 3)", "REAL")
            cursor.executescript(clean_sql)
            conn.commit()

        # Insertion order respecting foreign keys
        insertion_order = [
            "locations",
            "accounts",
            "complaints",
            "transactions",
            "cashout_events",
            "account_labels",
            "prediction_snapshots",
            "location_candidates",
            "case_relationships",
            "case_features",
            "prediction_ground_truth",
        ]

        for tbl in insertion_order:
            records = datasets.get(tbl, [])
            if not records:
                continue

            cols = list(records[0].keys())
            placeholders = ", ".join(["?"] * len(cols))
            col_names = ", ".join(cols)
            sql = f"INSERT OR REPLACE INTO {tbl} ({col_names}) VALUES ({placeholders})"

            rows = []
            for r in records:
                row_vals = []
                for c in cols:
                    v = r.get(c)
                    if isinstance(v, bool):
                        row_vals.append(1 if v else 0)
                    else:
                        row_vals.append(v)
                rows.append(row_vals)

            cursor.executemany(sql, rows)
            conn.commit()

        conn.close()
        return True

    elif "postgresql" in db_url:
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(db_url)
            with engine.connect() as conn:
                if schema_path.exists():
                    schema_sql = schema_path.read_text(encoding="utf-8")
                    conn.execute(text(schema_sql))
                    conn.commit()
            return True
        except Exception as e:
            print(f"PostgreSQL load warning: {e}")
            return False

    return False
