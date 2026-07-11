"""Registry of policyuncertainty.com data streams.

Each entry is a plain dict describing one downloadable file and how to turn
it into a tidy (date, value) or (date, column, value) table. `confidence`
tells you how sure this was at build time:

  - "confirmed"   - URL verified by fetching real data.
  - "best_guess"  - follows the site's naming convention but has not been
                    fetched and verified yet. Run `check_sources.py` to
                    confirm/fix these.

`shape`:
  - "long" - one row per date, one or more value columns already (e.g. a
             single country's daily/monthly file). Stored as-is.
  - "wide" - one row per date, one column per country/category (e.g. the
             all-country panel, or the categorical index file). Melted into
             (date, column, value) on ingest so you can filter one
             column/country out of a big multi-column file.

`date_mode`:
  - "ymd"  - separate year/month/day columns.
  - "ym"   - separate year/month columns (day defaults to 1).
  - "date" - a single date-like column.
"""

SERIES = [
    # -- Flagship series: confirmed URLs --------------------------------
    {
        "key": "US_MONTHLY",
        "country": "United States",
        "category": "EPU",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/US_Policy_Uncertainty_Data.xlsx",
        "file_type": "xlsx",
        "sheet_name": None,
        "date_mode": "ym",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/us_monthly.html",
        "confidence": "confirmed",
        "notes": "Baker, Bloom & Davis US monthly news-based EPU index.",
    },
    {
        "key": "US_DAILY",
        "country": "United States",
        "category": "EPU",
        "frequency": "daily",
        "url": "https://www.policyuncertainty.com/media/All_Daily_Policy_Data.csv",
        "file_type": "csv",
        "sheet_name": None,
        "date_mode": "ymd",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/us_monthly.html",
        "confidence": "confirmed",
        "notes": "Multi-column: includes the current and historical daily US EPU index variants.",
    },
    {
        "key": "UK_DAILY",
        "country": "United Kingdom",
        "category": "EPU",
        "frequency": "daily",
        "url": "https://www.policyuncertainty.com/media/UK_Daily_Policy_Data.csv",
        "file_type": "csv",
        "sheet_name": None,
        "date_mode": "ymd",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/uk_daily.html",
        "confidence": "confirmed",
        "notes": "The original series this project started from.",
    },

    # -- Panel files covering many countries at once: best guess ---------
    {
        "key": "ALL_COUNTRIES_MONTHLY",
        "country": None,
        "category": "EPU",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/All_Country_Data.xlsx",
        "file_type": "xlsx",
        "sheet_name": None,
        "date_mode": "ym",
        "shape": "wide",
        "source_page": "https://www.policyuncertainty.com/all_country_data.html",
        "confidence": "confirmed",
        "notes": (
            "One column per country (~20-40 countries) plus two GDP-weighted "
            "Global EPU columns (GEPU_ppp, GEPU_current). Filter with "
            "download('ALL_COUNTRIES_MONTHLY', column='United Kingdom')."
        ),
    },
    {
        "key": "US_CATEGORICAL",
        "country": "United States",
        "category": "Categorical EPU",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/Categorical_EPU_Data.xlsx",
        "file_type": "xlsx",
        "sheet_name": None,
        "date_mode": "ym",
        "shape": "wide",
        "source_page": "https://www.policyuncertainty.com/categorical_epu.html",
        "confidence": "confirmed",
        "notes": "One column per policy category (fiscal, monetary, trade, healthcare, etc.).",
    },

    # -- Specialty indices: best guess, lower confidence on filenames ----
    {
        "key": "TRADE_POLICY_UNCERTAINTY",
        "country": "United States",
        "category": "Trade Policy Uncertainty",
        "frequency": "daily",
        "url": "https://www.policyuncertainty.com/media/All_Daily_TPU_Data.csv",
        "file_type": "csv",
        "sheet_name": None,
        "date_mode": "ymd",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/trade_uncertainty.html",
        "confidence": "confirmed",
        "notes": "Daily trade policy uncertainty index. Monthly trade data lives in US_CATEGORICAL.",
    },
    {
        "key": "MONETARY_POLICY_UNCERTAINTY",
        "country": "United States",
        "category": "Monetary Policy Uncertainty",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/US_MPU_Monthly.xlsx",
        "file_type": "xlsx",
        "sheet_name": None,
        "date_mode": "ym",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/bbd_monetary.html",
        "confidence": "confirmed",
        "notes": "Baker-Bloom-Davis MPU index.",
    },
    {
        "key": "CLIMATE_POLICY_UNCERTAINTY",
        "country": "United States",
        "category": "Climate Policy Uncertainty",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/cpu_pu.xlsx",
        "file_type": "xlsx",
        "sheet_name": "data",
        "date_mode": "ym_stata",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/climate_uncertainty.html",
        "confidence": "confirmed",
        "notes": "Gavriilidis Climate Policy Uncertainty index.",
    },
    {
        "key": "US_STATE_EPU",
        "country": "United States",
        "category": "State-level EPU",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/State_Policy_Uncertainty.xlsx",
        "file_type": "xlsx",
        "sheet_name": None,
        "date_mode": "ym",
        "shape": "wide",
        "source_page": "https://www.policyuncertainty.com/state_epu.html",
        "confidence": "confirmed",
        "notes": "One column per US state.",
    },
    {
        "key": "US_CHINA_TENSION",
        "country": None,
        "category": "US-China Tension",
        "frequency": "monthly",
        "url": "https://www.policyuncertainty.com/media/UCT.csv",
        "file_type": "csv",
        "sheet_name": None,
        "date_mode": "ym_stata",
        "shape": "long",
        "source_page": "https://www.policyuncertainty.com/US_China_Tension.html",
        "confidence": "confirmed",
        "notes": "Rogers, Sun & Sun (2024) US-China Tension index. Date column uses Stata format (e.g. 1993m1).",
    },
]


def get(key: str) -> dict:
    for entry in SERIES:
        if entry["key"] == key:
            return entry
    raise KeyError(
        f"Unknown series '{key}'. See policyuncertainty.available() for valid keys."
    )


def keys() -> list[str]:
    return [e["key"] for e in SERIES]
