"""Verify every registry URL actually works, from your own network.

Run this periodically to catch upstream filename/layout changes (see
`confidence` in economicpolicyuncertainty/registry.py):

    python check_sources.py

For each series it reports OK (fetched + parsed successfully, with row/column
counts) or FAILED (with the error) so you know exactly what to fix and where
(edit the `url` in economicpolicyuncertainty/registry.py).
"""
import logging

from economicpolicyuncertainty import fetch, registry

logging.basicConfig(level=logging.WARNING)  # quiet the fetch module's own logs here


def main():
    print(f"Checking {len(registry.SERIES)} registry entries against the live site...\n")
    ok, failed = [], []
    for entry in registry.SERIES:
        label = f"{entry['key']:28s} [{entry['confidence']}]"
        try:
            content = fetch.download_bytes(entry["url"], referer=entry.get("source_page"))
            rows = fetch.parse(content, entry)
            n = len(rows)
            cols = len({r.get("column") for r in rows}) if entry["shape"] == "wide" else None
            extra = f", {cols} columns" if cols else ""
            print(f"OK      {label} -> {n} rows{extra}")
            ok.append(entry["key"])
        except Exception as e:  # noqa: BLE001
            print(f"FAILED  {label} -> {e}")
            failed.append(entry["key"])

    print(f"\n{len(ok)} ok, {len(failed)} failed.")
    if failed:
        print("Fix these in economicpolicyuncertainty/registry.py:", ", ".join(failed))


if __name__ == "__main__":
    main()
