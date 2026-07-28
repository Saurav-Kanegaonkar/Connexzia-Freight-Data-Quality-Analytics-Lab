"""Create documented synthetic dispatch, event, and reporting-run source extracts."""
from __future__ import annotations

import csv
import random
from datetime import date, datetime, timedelta
from pathlib import Path

random.seed(20260728)
ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

carriers = [("Northline Freight", "West"), ("Desert Haul", "Southwest"), ("Pinnacle Transport", "West"), ("Sunbelt Logistics", "Southwest"), ("Canyon Express", "West")]
lanes = [("Phoenix", "Los Angeles", 371), ("Phoenix", "Dallas", 1065), ("Scottsdale", "Denver", 918), ("Tucson", "Las Vegas", 414), ("Phoenix", "Salt Lake City", 664)]
start = date(2026, 1, 1)
shipments = []
events = []
for i in range(1, 1201):
    carrier, region = carriers[(i - 1) % len(carriers)]
    origin, destination, miles = lanes[(i * 3) % len(lanes)]
    booked = start + timedelta(days=(i * 7) % 180)
    planned = booked + timedelta(days=2 + (i % 4))
    late = random.random() < (0.07 + (0.06 if carrier == "Desert Haul" else 0))
    delivered = planned + timedelta(days=(1 if late else 0))
    linehaul = round(miles * random.uniform(1.75, 2.4), 2)
    eta_missing = 1 if i % 67 == 0 else 0
    pod_missing = 1 if i % 83 == 0 else 0
    ship = {
        "shipment_id": f"SHP{i:05d}", "booked_date": booked.isoformat(), "carrier_id": f"CAR{(i - 1) % 5 + 1:03d}",
        "origin": origin, "destination": destination, "region": region, "planned_delivery_date": planned.isoformat(),
        "actual_delivery_date": delivered.isoformat(), "miles": miles, "linehaul_usd": linehaul,
        "eta_missing_flag": eta_missing, "pod_missing_flag": pod_missing, "on_time_flag": int(not late)
    }
    shipments.append(ship)
    for typ, offset in [("booked", 0), ("pickup_confirmed", 1), ("in_transit", 2), ("delivered", (delivered-booked).days)]:
        events.append({"event_id": f"EVT{i:05d}_{typ}", "shipment_id": ship["shipment_id"], "event_type": typ,
                       "event_timestamp": (datetime.combine(booked + timedelta(days=offset), datetime.min.time()) + timedelta(hours=(i * 3 + offset) % 24)).isoformat(),
                       "source_system": "dispatch_tms" if typ != "delivered" else "carrier_portal"})

with (DATA / "carriers.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=["carrier_id", "carrier_name", "region", "contracted_rate_per_mile"]); w.writeheader()
    for j, (name, region) in enumerate(carriers, 1): w.writerow({"carrier_id": f"CAR{j:03d}", "carrier_name": name, "region": region, "contracted_rate_per_mile": round(1.95 + j*.08, 2)})
with (DATA / "shipments.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=shipments[0].keys()); w.writeheader(); w.writerows(shipments)
with (DATA / "shipment_events.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=events[0].keys()); w.writeheader(); w.writerows(events)
with (DATA / "report_runs.csv").open("w", newline="") as f:
    fields = ["run_id", "run_date", "scheduled_at", "completed_at", "status", "records_processed", "exception_count"]
    w = csv.DictWriter(f, fieldnames=fields); w.writeheader()
    for i in range(1, 181):
        day = start + timedelta(days=i-1); fail = i % 37 == 0; late_run = i % 19 == 0
        w.writerow({"run_id": f"RUN{i:04d}", "run_date": day.isoformat(), "scheduled_at": f"{day}T06:00:00", "completed_at": f"{day}T{('09:05:00' if late_run else '06:18:00')}", "status": "failed" if fail else "success", "records_processed": 310 + (i % 55), "exception_count": 3 + (i % 9) + (12 if fail else 0)})
