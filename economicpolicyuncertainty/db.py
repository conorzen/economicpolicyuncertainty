"""Generic SQLite storage - one table per registry series.

'long' shape series get a table keyed by `date` with one column per field in
the source file. 'wide' shape series (melted on ingest) get a table keyed by
(date, column) so a single file with many countries/categories can still be
queried for just one of them.
"""
import re
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "economicpolicyuncertainty.db"


def _sanitize(col: str) -> str:
    col = col.strip().lower()
    col = re.sub(r"[^a-z0-9_]+", "_", col)
    col = re.sub(r"_+", "_", col).strip("_")
    return col or "value"


def sanitize_columns(columns):
    seen = {}
    out = []
    for c in columns:
        base = _sanitize(str(c))
        n = seen.get(base, 0)
        seen[base] = n + 1
        out.append(base if n == 0 else f"{base}_{n}")
    return out


def _table_name(key: str) -> str:
    return "series_" + _sanitize(key)


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_table(key: str, columns, shape: str):
    table = _table_name(key)
    conn = get_connection()
    if shape == "wide":
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{table}" ('
            '"date" TEXT NOT NULL, "column" TEXT NOT NULL, "value" TEXT, '
            'PRIMARY KEY ("date", "column"))'
        )
    else:
        cols_sql = ", ".join(f'"{c}" TEXT' for c in columns if c != "date")
        conn.execute(
            f'CREATE TABLE IF NOT EXISTS "{table}" ("date" TEXT PRIMARY KEY'
            + (f", {cols_sql}" if cols_sql else "")
            + ")"
        )
    conn.commit()
    conn.close()


def upsert_rows(key: str, rows: list[dict], shape: str) -> int:
    if not rows:
        return 0
    columns = list(rows[0].keys())
    ensure_table(key, columns, shape)
    table = _table_name(key)
    conn = get_connection()
    placeholders = ", ".join(f":{c}" for c in columns)
    col_list = ", ".join(f'"{c}"' for c in columns)
    before = conn.total_changes
    conn.executemany(
        f'INSERT OR IGNORE INTO "{table}" ({col_list}) VALUES ({placeholders})',
        rows,
    )
    conn.commit()
    inserted = conn.total_changes - before
    conn.close()
    return inserted


def all_rows(key: str, start=None, end=None, column=None):
    table = _table_name(key)
    conn = get_connection()
    query = f'SELECT * FROM "{table}"'
    clauses, params = [], {}
    if start:
        clauses.append('"date" >= :start')
        params["start"] = start
    if end:
        clauses.append('"date" <= :end')
        params["end"] = end
    if column:
        clauses.append('"column" = :column')
        params["column"] = _sanitize(column)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += ' ORDER BY "date" ASC'
    try:
        rows = conn.execute(query, params).fetchall()
    except sqlite3.OperationalError:
        rows = []
    conn.close()
    return [dict(r) for r in rows]


def distinct_columns(key: str):
    """For a 'wide' series, list the country/category names available."""
    table = _table_name(key)
    conn = get_connection()
    try:
        rows = conn.execute(f'SELECT DISTINCT "column" FROM "{table}" ORDER BY 1').fetchall()
        result = [r["column"] for r in rows]
    except sqlite3.OperationalError:
        result = []
    conn.close()
    return result


def latest_row(key: str, column=None):
    table = _table_name(key)
    conn = get_connection()
    query = f'SELECT * FROM "{table}"'
    params = {}
    if column:
        query += ' WHERE "column" = :column'
        params["column"] = _sanitize(column)
    query += ' ORDER BY "date" DESC LIMIT 1'
    try:
        row = conn.execute(query, params).fetchone()
    except sqlite3.OperationalError:
        row = None
    conn.close()
    return dict(row) if row else None


def row_count(key: str) -> int:
    table = _table_name(key)
    conn = get_connection()
    try:
        n = conn.execute(f'SELECT COUNT(*) AS n FROM "{table}"').fetchone()["n"]
    except sqlite3.OperationalError:
        n = 0
    conn.close()
    return n
