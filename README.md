# economicpolicyuncertainty

A yfinance-style Python client for [policyuncertainty.com](https://www.policyuncertainty.com).
Fetch any EPU index as a pandas DataFrame, cached locally in SQLite so repeat
calls don't re-hit the source.

## Installation

```bash
pip install economicpolicyuncertainty
```

With the optional REST server:

```bash
pip install economicpolicyuncertainty[server]
```

## Quick start

```python
import economicpolicyuncertainty as pu

pu.available()                                        # DataFrame of every series
pu.download("UK_DAILY", refresh=True)                 # fetch + return DataFrame indexed by date
pu.download("ALL_COUNTRIES_MONTHLY", column="UK")     # one country from the panel file

s = pu.Series("UK_DAILY")
s.info                                                # registry metadata dict
s.history(start="2020-01-01", end="2020-12-31")       # filtered DataFrame
s.columns()                                           # for wide series, list available columns
s.latest()                                            # most recent record as a dict
s.refresh()                                           # force re-fetch from source

pu.refresh_all()                                      # refresh every series; failures are isolated
```

## Indicators

| Key | Description | Frequency | Coverage |
|-----|-------------|-----------|----------|
| `US_MONTHLY` | Baker, Bloom & Davis US EPU index | Monthly | 1985 – present |
| `US_DAILY` | Multi-variant daily US EPU index | Daily | 1985 – present |
| `UK_DAILY` | UK daily EPU index | Daily | 2001 – present |
| `ALL_COUNTRIES_MONTHLY` | ~24-country EPU panel + global GEPU | Monthly | 1985 – present |
| `US_CATEGORICAL` | US EPU broken out by policy category | Monthly | 1985 – present |
| `TRADE_POLICY_UNCERTAINTY` | Daily US trade policy uncertainty (TPU) | Daily | 1985 – present |
| `MONETARY_POLICY_UNCERTAINTY` | Baker-Bloom-Davis US monetary policy uncertainty | Monthly | 1985 – present |
| `CLIMATE_POLICY_UNCERTAINTY` | Gavriilidis et al. climate policy uncertainty | Monthly | 1985 – present |
| `US_STATE_EPU` | State-level EPU, one column per US state | Monthly | 1985 – present |
| `US_CHINA_TENSION` | Rogers, Sun & Sun US-China tension index | Monthly | 1993 – present |

### Multi-column series

`ALL_COUNTRIES_MONTHLY`, `US_CATEGORICAL`, and `US_STATE_EPU` each contain many
columns in a single file. Use `column=` to filter to one, or `.columns()` to see
what's available:

```python
s = pu.Series("ALL_COUNTRIES_MONTHLY")
s.columns()
# ['australia', 'brazil', 'canada', 'chile', 'china', 'france',
#  'gepu_current', 'gepu_ppp', 'germany', 'greece', 'india', 'ireland',
#  'italy', 'japan', 'korea', 'mainland_china', 'mexico', 'pakistan',
#  'russia', 'scmp_china', 'singapore', 'spain', 'uk', 'us']

pu.download("ALL_COUNTRIES_MONTHLY", column="uk")

s = pu.Series("US_CATEGORICAL")
s.columns()
# ['1_economic_policy_uncertainty', '2_monetary_policy', '3_taxes',
#  '4_government_spending', '5_health_care', '6_national_security',
#  '7_entitlement_programs', '8_regulation', '9_trade_policy',
#  '10_sovereign_debt_currency_crises', 'financial_regulation',
#  'fiscal_policy_taxes_or_spending']
```

Column names are lowercased and have spaces replaced with underscores. Pass
either the raw name (`"United Kingdom"`) or the sanitized form (`"uk"`) —
both work.

## API reference

### `pu.available() → DataFrame`
Returns a DataFrame listing every series and its metadata (key, frequency,
shape, url, notes).

### `pu.download(key, start=None, end=None, column=None, refresh=False) → DataFrame`
Returns the series as a DataFrame indexed by date. Reads from the local cache
by default; pass `refresh=True` to fetch fresh data first.

### `pu.Series(key)`
Object-oriented interface to a single series.

| Method | Returns |
|--------|---------|
| `.history(start, end, column)` | DataFrame |
| `.columns()` | list of column names (wide series only) |
| `.latest(column)` | most recent record as a dict |
| `.refresh()` | re-fetches from source, returns stats dict |
| `.info` | registry metadata dict |

### `pu.refresh_all() → list[dict]`
Refreshes every series. Each failure is caught individually so one bad URL
doesn't block the rest.

## Local REST API (optional)

Useful for accessing data from non-Python environments.

```bash
python server.py          # runs at http://127.0.0.1:5000
```

Refreshes all series on startup, then daily at 06:00 local time
(`REFRESH_HOUR` / `REFRESH_MINUTE` env vars to change it).

| Endpoint | Description |
|----------|-------------|
| `GET /api/series` | all series + metadata |
| `GET /api/series/<key>` | data as JSON (`?start=&end=&column=`) |
| `GET /api/series/<key>/columns` | available columns for wide series |
| `GET /api/series/<key>/latest` | most recent record |
| `POST /api/series/<key>/refresh` | force re-fetch of one series |
| `POST /api/refresh-all` | force re-fetch of everything |

## Handling the source's bot check

The site occasionally serves a JavaScript challenge page to automated requests.
Every fetch tries a browser-header `requests` session first, then falls back to
`cloudscraper`. If both fail, download the file manually and feed it in:

```python
from economicpolicyuncertainty import fetch, db, registry

entry = registry.get("UK_DAILY")
with open("UK_Daily_Policy_Data.csv", "rb") as f:
    rows = fetch.parse(f.read(), entry)
db.upsert_rows(entry["key"], rows, shape=entry["shape"])
```

## Verifying sources

If a series stops returning data, run:

```bash
python check_sources.py
```

It reports `OK <rows>` or `FAILED <error>` for every registry entry. A broken
URL is a one-line fix in `policyuncertainty/registry.py`.
