# Changelog

## [0.1.1] - 2026-07-11

### Fixed
- `Series.columns()` / `.latest()` / `download(column=...)` raised a confusing
  `IndexError` when called on a "long" shape series (e.g. `UK_DAILY`), which
  has no `column` field. They now correctly treat `column` filtering as
  wide-series-only, returning `[]` from `.columns()` on long series instead
  of crashing.

## [0.1.0] - 2026-07-11

Initial release. 10 EPU-family series (US, UK, global panel, categorical,
trade/monetary/climate/state-level, US-China tension), SQLite-cached, with
an optional Flask REST server.
