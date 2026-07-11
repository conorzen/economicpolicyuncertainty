"""A python client for policyuncertainty.com data.

    import economicpolicyuncertainty as epu

    pu.available()                          # DataFrame of every known series
    pu.download("UK_DAILY")                 # DataFrame indexed by date
    pu.download("ALL_COUNTRIES_MONTHLY", column="UK")

    s = pu.Series("UK_DAILY")
    s.info                                  # registry metadata dict
    s.history(start="2020-01-01")           # DataFrame
    s.refresh()                             # force re-fetch from source

    pu.refresh_all()                        # refresh every series, isolating failures
"""
from __future__ import annotations

import logging

import pandas as pd

from . import db, fetch, registry

log = logging.getLogger("economicpolicyuncertainty")

__all__ = ["available", "download", "Series", "refresh_all"]


def available() -> pd.DataFrame:
    """List every known series and its metadata."""
    return pd.DataFrame(registry.SERIES)[
        [
            "key",
            "country",
            "category",
            "frequency",
            "shape",
            "confidence",
            "url",
            "notes",
        ]
    ]


def _rows_to_frame(entry: dict, rows: list[dict]) -> pd.DataFrame:
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date").sort_index()
    for col in df.columns:
        if col == "column":  # category/country label in wide series - stays a string
            continue
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df


def download(
    key: str,
    start: str | None = None,
    end: str | None = None,
    column: str | None = None,
    refresh: bool = False,
) -> pd.DataFrame:
    """Return a series as a DataFrame indexed by date, straight from local
    storage. Pass `refresh=True` to fetch fresh data first. For 'wide'
    series (many countries/categories in one file), pass `column=` to filter
    to just one (see `Series(key).columns()` for the available names)."""
    entry = registry.get(key)
    if refresh:
        fetch.refresh(entry)
    rows = db.all_rows(key, start=start, end=end, column=column)
    return _rows_to_frame(entry, rows)


def refresh_all() -> list[dict]:
    """Refresh every series in the registry. Each failure is caught and
    reported individually so one bad URL doesn't stop the rest."""
    results = []
    for entry in registry.SERIES:
        try:
            results.append(fetch.refresh(entry))
        except Exception as e:  # noqa: BLE001
            log.warning("refresh failed for %s: %s", entry["key"], e)
            results.append({"key": entry["key"], "error": str(e)})
    return results


class Series:
    """A single data stream, e.g. Series('UK_DAILY')."""

    def __init__(self, key: str):
        self.key = key
        self.info = registry.get(key)

    def history(
        self,
        start: str | None = None,
        end: str | None = None,
        column: str | None = None,
    ) -> pd.DataFrame:
        rows = db.all_rows(self.key, start=start, end=end, column=column)
        return _rows_to_frame(self.info, rows)

    def columns(self) -> list[str]:
        """For a 'wide' series, the country/category names available."""
        return db.distinct_columns(self.key)

    def latest(self, column: str | None = None) -> dict | None:
        return db.latest_row(self.key, column=column)

    def refresh(self) -> dict:
        return fetch.refresh(self.info)

    def __repr__(self) -> str:
        return f"Series({self.key!r}, rows={db.row_count(self.key)})"
