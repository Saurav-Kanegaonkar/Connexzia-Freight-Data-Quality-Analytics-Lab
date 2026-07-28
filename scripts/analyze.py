"""Reproducibly summarize synthetic freight dispatch reliability and quality controls."""
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]; DATA = ROOT / "data"; OUT = ROOT / "analysis" / "outputs"; IMG = ROOT / "docs" / "images"
OUT.mkdir(parents=True, exist_ok=True); IMG.mkdir(parents=True, exist_ok=True)
s = pd.read_csv(DATA / "shipments.csv", parse_dates=["booked_date", "planned_delivery_date", "actual_delivery_date"])
r = pd.read_csv(DATA / "report_runs.csv", parse_dates=["run_date", "scheduled_at", "completed_at"])
s["quality_exception"] = ((s.eta_missing_flag == 1) | (s.pod_missing_flag == 1)).astype(int)
carrier = s.groupby("carrier_id").agg(shipments=("shipment_id","count"), on_time_rate=("on_time_flag","mean"), quality_exception_rate=("quality_exception","mean"), avg_linehaul_usd=("linehaul_usd","mean")).reset_index()
carrier.to_csv(OUT / "carrier_scorecard.csv", index=False)
r["sla_met"] = ((r.status == "success") & ((r.completed_at-r.scheduled_at).dt.total_seconds() <= 3600)).astype(int)
daily = r.groupby("run_date").agg(refresh_sla_rate=("sla_met","mean"), exceptions=("exception_count","sum")).reset_index()
daily.to_csv(OUT / "refresh_reliability.csv", index=False)
summary = {"shipments": len(s), "event_rows": len(pd.read_csv(DATA / "shipment_events.csv")), "on_time_rate": round(s.on_time_flag.mean()*100,1), "quality_exception_rate": round(s.quality_exception.mean()*100,1), "refresh_sla_rate": round(r.sla_met.mean()*100,1)}
pd.DataFrame([summary]).to_csv(OUT / "kpi_summary.csv", index=False)
plt.style.use("seaborn-v0_8-whitegrid")
fig, ax = plt.subplots(figsize=(9,4.8)); ordered=carrier.sort_values("on_time_rate")
ax.bar(ordered.carrier_id, ordered.on_time_rate*100, color=["#d95f02" if x < .90 else "#1b9e77" for x in ordered.on_time_rate]); ax.axhline(90,color="#555",ls="--",lw=1); ax.set_ylim(70,100); ax.set_ylabel("On-time delivery (%)"); ax.set_title("Carrier reliability scorecard"); fig.tight_layout(); fig.savefig(IMG / "carrier_reliability.png", dpi=160); plt.close(fig)
fig, ax1 = plt.subplots(figsize=(9,4.8)); ax1.plot(daily.run_date, daily.refresh_sla_rate*100, color="#276fbf", label="Refresh SLA met"); ax1.set_ylim(0,105); ax1.set_ylabel("SLA met (%)"); ax1.set_title("Automated reporting refresh reliability"); ax1.tick_params(axis="x", rotation=25); ax2=ax1.twinx(); ax2.plot(daily.run_date, daily.exceptions, color="#d95f02", alpha=.65, label="Exceptions"); ax2.set_ylabel("Exceptions"); fig.tight_layout(); fig.savefig(IMG / "refresh_reliability.png", dpi=160); plt.close(fig)
