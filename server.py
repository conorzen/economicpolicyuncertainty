"""REST API wrapping the `economicpolicyuncertainty` package, covering every series
in the registry.

Run:
    pip install -r requirements.txt
    python server.py

Endpoints:
    GET  /api/series                       -> list every known series + metadata
    GET  /api/series/<key>                 -> data as JSON
                                               optional ?start=&end=&column=
    GET  /api/series/<key>/columns         -> for 'wide' series, the country/
                                               category names actually stored
    GET  /api/series/<key>/latest          -> most recent record (optional ?column=)
    POST /api/series/<key>/refresh         -> force re-fetch of just this series
    POST /api/refresh-all                  -> force re-fetch of every series

A background job refreshes every series once a day (default 06:00 local
time; configurable with REFRESH_HOUR / REFRESH_MINUTE).
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, jsonify, request

import economicpolicyuncertainty as pu
from economicpolicyuncertainty import db, fetch, registry

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("economicpolicyuncertainty.server")

app = Flask(__name__)


@app.get("/api/series")
def list_series():
    return jsonify(registry.SERIES)


@app.get("/api/series/<key>")
def get_series(key):
    try:
        entry = registry.get(key)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    rows = db.all_rows(
        key,
        start=request.args.get("start"),
        end=request.args.get("end"),
        column=request.args.get("column"),
    )
    return jsonify({"key": key, "shape": entry["shape"], "rows": rows})


@app.get("/api/series/<key>/columns")
def get_columns(key):
    try:
        registry.get(key)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    return jsonify(db.distinct_columns(key))


@app.get("/api/series/<key>/latest")
def get_latest(key):
    try:
        registry.get(key)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    row = db.latest_row(key, column=request.args.get("column"))
    if row is None:
        return jsonify({"error": "no data yet - POST /api/series/<key>/refresh first"}), 404
    return jsonify(row)


@app.post("/api/series/<key>/refresh")
def refresh_one(key):
    try:
        entry = registry.get(key)
    except KeyError as e:
        return jsonify({"error": str(e)}), 404
    try:
        return jsonify(fetch.refresh(entry))
    except Exception as e:  # noqa: BLE001
        log.exception("refresh failed for %s", key)
        return jsonify({"key": key, "error": str(e)}), 502


@app.post("/api/refresh-all")
def refresh_all():
    return jsonify(pu.refresh_all())


def _scheduled_refresh():
    results = pu.refresh_all()
    ok = [r for r in results if "error" not in r]
    failed = [r for r in results if "error" in r]
    log.info("daily refresh: %d ok, %d failed %s", len(ok), len(failed), failed)


def start_scheduler():
    hour = int(os.environ.get("REFRESH_HOUR", 6))
    minute = int(os.environ.get("REFRESH_MINUTE", 0))
    scheduler = BackgroundScheduler()
    scheduler.add_job(_scheduled_refresh, "cron", hour=hour, minute=minute)
    scheduler.start()
    log.info("Daily refresh of all series scheduled for %02d:%02d local time", hour, minute)
    return scheduler


if __name__ == "__main__":
    start_scheduler()
    log.info("Running initial refresh of all series (failures are logged, not fatal)...")
    for result in pu.refresh_all():
        log.info(result)
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)))
