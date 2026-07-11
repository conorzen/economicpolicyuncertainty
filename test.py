"""Integration test — hits the live site.

Run with:
    uv run python test.py
"""
import sys
import traceback

import economicpolicyuncertainty as pu


def section(title):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print('=' * 60)


def check(label, value, expected=None):
    if expected is not None:
        ok = value == expected
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {label}: {value!r} (expected {expected!r})")
        return ok
    print(f"  [INFO] {label}: {value!r}")
    return True


passed, failed = [], []


def run(label, fn):
    try:
        fn()
        passed.append(label)
    except Exception:
        failed.append(label)
        print(f"  [FAIL] {label}")
        traceback.print_exc()


# ── 1. available() ────────────────────────────────────────────────────────────
section("pu.available()")

def test_available():
    df = pu.available()
    check("returns a DataFrame", type(df).__name__, "DataFrame")
    check("10 series in registry", len(df), 10)
    check("has key column", "key" in df.columns, True)
    print(df[["key", "frequency", "confidence"]].to_string(index=False))

run("available()", test_available)


# ── 2. download() — confirmed long series ─────────────────────────────────────
section("pu.download('UK_DAILY', refresh=True)")

def test_uk_daily():
    df = pu.download("UK_DAILY", refresh=True)
    check("returns a DataFrame", type(df).__name__, "DataFrame")
    check("has rows", len(df) > 0, True)
    check("index is DatetimeIndex", df.index.dtype.kind, "M")
    print(f"  rows: {len(df)}, date range: {df.index[0].date()} → {df.index[-1].date()}")
    print(df.tail(3).to_string())
    # regression: .columns() on a 'long' series must return [], not raise
    check("columns() on long series returns []", pu.Series("UK_DAILY").columns(), [])

run("download UK_DAILY", test_uk_daily)


# ── 3. download() — date filtering ────────────────────────────────────────────
section("pu.download('UK_DAILY', start=..., end=...)")

def test_date_filter():
    df = pu.download("UK_DAILY", start="2020-01-01", end="2020-12-31")
    check("rows within 2020", len(df) > 0, True)
    check("start >= 2020-01-01", str(df.index[0].date()) >= "2020-01-01", True)
    check("end <= 2020-12-31", str(df.index[-1].date()) <= "2020-12-31", True)
    print(f"  rows in 2020: {len(df)}")

run("download with date filter", test_date_filter)


# ── 4. wide series — column filtering ─────────────────────────────────────────
section("pu.download('ALL_COUNTRIES_MONTHLY', column='UK')")

def test_wide_column():
    df = pu.download("ALL_COUNTRIES_MONTHLY", refresh=True, column="UK")
    check("returns a DataFrame", type(df).__name__, "DataFrame")
    check("has rows", len(df) > 0, True)
    print(f"  rows: {len(df)}, date range: {df.index[0].date()} → {df.index[-1].date()}")
    print(df.tail(3).to_string())

run("download ALL_COUNTRIES_MONTHLY (UK column)", test_wide_column)


# ── 5. Series API ─────────────────────────────────────────────────────────────
section("pu.Series('ALL_COUNTRIES_MONTHLY')")

def test_series_api():
    s = pu.Series("ALL_COUNTRIES_MONTHLY")
    check("info is a dict", type(s.info).__name__, "dict")
    cols = s.columns()
    check("columns() returns a list", type(cols).__name__, "list")
    check("has >= 1 column", len(cols) >= 1, True)
    print(f"  available columns ({len(cols)}): {cols[:5]}{'...' if len(cols) > 5 else ''}")
    latest = s.latest(column=cols[0])
    check("latest() returns a dict", type(latest).__name__, "dict")
    print(f"  latest ({cols[0]}): {latest}")

run("Series API", test_series_api)


# ── 6. specialty series ────────────────────────────────────────────────────────
section("Specialty series (refresh each)")

for key in [
    "TRADE_POLICY_UNCERTAINTY",
    "MONETARY_POLICY_UNCERTAINTY",
    "CLIMATE_POLICY_UNCERTAINTY",
    "US_STATE_EPU",
    "US_CHINA_TENSION",
]:
    def test_specialty(k=key):
        df = pu.download(k, refresh=True)
        check(f"{k}: has rows", len(df) > 0, True)
        print(f"  rows: {len(df)}, date range: {df.index[0].date()} → {df.index[-1].date()}")

    run(f"download {key}", test_specialty)


# ── Summary ───────────────────────────────────────────────────────────────────
section("Summary")
print(f"  passed: {len(passed)}")
print(f"  failed: {len(failed)}")
if failed:
    print(f"  failed tests: {', '.join(failed)}")
    sys.exit(1)
else:
    print("  All tests passed.")
