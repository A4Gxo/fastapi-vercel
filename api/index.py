# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics

app = FastAPI()

# ✅ Enable CORS for any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Analytics API running"}

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    # Load telemetry file
    with open("q-vercel-latency.json", "r") as f:
        data = json.load(f)

    # Group by region
    region_metrics = {}
    for region in regions:
        records = [r for r in data if r["region"] == region]
        if not records:
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        avg_latency = sum(latencies) / len(latencies)
        p95_latency = statistics.quantiles(latencies, n=100)[94]  # 95th percentile
        avg_uptime = sum(uptimes) / len(uptimes)
        breaches = sum(1 for x in latencies if x > threshold)

        region_metrics[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    return region_metrics
