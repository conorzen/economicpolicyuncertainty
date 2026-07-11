"""Generic downloader + parser for any policyuncertainty.com data file.

Handles two problems uniformly across every series in the registry:

1. Bot check: the site returns a "JavaScript is required" page to plain
   automated requests. We try a real-browser-header `requests` session first,
   then fall back to `cloudscraper` (solves simple JS/Cloudflare challenges
   without a real browser).
2. Unknown exact layout: Excel/CSV files on this site sometimes have a
   couple of preamble/notes rows above the real header. We scan the first
   few rows for something that looks like a header (contains "year" or
   "date") instead of assuming row 0.
"""
from __future__ import annotations

import io
import logging
from datetime import datetime

import pandas as pd
import requests

from . import db

log = logging.getLogger("economicpolicyuncertainty.fetch")

INDEX_URL = "https://www.policyuncertainty.com/"

BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": INDEX_URL,
}


class FetchBlockedError(RuntimeError):
    pass


def _looks_like_block_page(content: bytes) -> bool:
    head = content[:2000].lower()
    return b"javascript is required" in head


def _download_via_requests(url: str, referer: str) -> bytes:
    session = requests.Session()
    headers = dict(BROWSER_HEADERS, Referer=referer)
    session.headers.update(headers)
    session.get(referer, timeout=20)  # pick up any cookies set on first visit
    resp = session.get(url, timeout=30)
    resp.raise_for_status()
    if _looks_like_block_page(resp.content):
        raise FetchBlockedError("plain requests session got the JS-check page")
    return resp.content


def _download_via_cloudscraper(url: str) -> bytes:
    import cloudscraper

    scraper = cloudscraper.create_scraper(browser={"custom": BROWSER_HEADERS["User-Agent"]})
    resp = scraper.get(url, timeout=30)
    resp.raise_for_status()
    if _looks_like_block_page(resp.content):
        raise FetchBlockedError("cloudscraper still got the JS-check page")
    return resp.content


def download_bytes(url: str, referer: str = INDEX_URL) -> bytes:
    try:
        return _download_via_requests(url, referer)
    except Exception as e:  # noqa: BLE001
        log.warning("plain requests fetch of %s failed (%s); trying cloudscraper", url, e)
    return _download_via_cloudscraper(url)


def _find_header_row(raw_df: pd.DataFrame, max_scan: int = 10) -> int:
    """Scan the first few rows for one that looks like a real header
    (contains 'year' or 'date'), for files with preamble/notes rows."""
    for i in range(min(max_scan, len(raw_df))):
        row_vals = [str(v).strip().lower() for v in raw_df.iloc[i].tolist()]
        if any(v in ("year", "date") for v in row_vals):
            return i
    return 0


def _read_table(content: bytes, entry: dict) -> pd.DataFrame:
    if entry["file_type"] == "csv":
        raw = pd.read_csv(io.BytesIO(content), header=None, dtype=str)
    elif entry["file_type"] == "xlsx":
        raw = pd.read_excel(
            io.BytesIO(content), sheet_name=entry.get("sheet_name") or 0, header=None
        )
    else:
        raise ValueError(f"Unsupported file_type: {entry['file_type']}")

    header_row = _find_header_row(raw)
    df = raw.iloc[header_row + 1 :].copy()
    df.columns = [str(c) for c in raw.iloc[header_row].tolist()]
    df = df.dropna(how="all")
    return df.reset_index(drop=True)


def _build_date(df: pd.DataFrame, date_mode: str) -> pd.Series:
    if date_mode == "ymd":
        if not {"year", "month", "day"}.issubset(df.columns):
            raise ValueError(f"Expected year/month/day columns, got: {list(df.columns)}")
        return pd.to_datetime(
            df[["year", "month", "day"]], errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    if date_mode == "ym":
        if not {"year", "month"}.issubset(df.columns):
            raise ValueError(f"Expected year/month columns, got: {list(df.columns)}")
        return pd.to_datetime(
            df["year"].astype(str) + "-" + df["month"].astype(str) + "-01",
            errors="coerce",
        ).dt.strftime("%Y-%m-%d")
    if date_mode == "date":
        if "date" not in df.columns:
            raise ValueError(f"Expected a date column, got: {list(df.columns)}")
        return pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if date_mode == "ym_stata":
        # Handles Stata-style period strings like "1993m1"
        if "date" not in df.columns:
            raise ValueError(f"Expected a date column, got: {list(df.columns)}")
        parts = df["date"].str.extract(r"^(\d{4})[mM](\d+)$")
        return pd.to_datetime(
            parts[0] + "-" + parts[1] + "-01", errors="coerce"
        ).dt.strftime("%Y-%m-%d")
    raise ValueError(f"Unknown date_mode: {date_mode}")


def parse(content: bytes, entry: dict) -> list[dict]:
    df = _read_table(content, entry)
    df.columns = db.sanitize_columns(df.columns)

    date = _build_date(df, entry["date_mode"])
    df = df.assign(date=date)
    drop_cols = [c for c in ("year", "month", "day") if c in df.columns and c != "date"]
    value_df = df.drop(columns=drop_cols)
    value_df = value_df.dropna(subset=["date"])
    value_df = value_df.dropna(how="all", axis=1)

    if entry["shape"] == "long":
        cols = ["date"] + [c for c in value_df.columns if c != "date"]
        return value_df[cols].to_dict(orient="records")

    if entry["shape"] == "wide":
        long_df = value_df.melt(id_vars=["date"], var_name="column", value_name="value")
        long_df = long_df.dropna(subset=["value"])
        return long_df.to_dict(orient="records")

    raise ValueError(f"Unknown shape: {entry['shape']}")


def refresh(entry: dict) -> dict:
    content = download_bytes(entry["url"], referer=entry.get("source_page", INDEX_URL))
    rows = parse(content, entry)
    inserted = db.upsert_rows(entry["key"], rows, shape=entry["shape"])
    return {
        "key": entry["key"],
        "fetched_at": datetime.utcnow().isoformat() + "Z",
        "rows_seen": len(rows),
        "rows_inserted": inserted,
        "total_rows": db.row_count(entry["key"]),
    }
