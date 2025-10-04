from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics
import os

app = FastAPI()

# ✅ Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data once when the function starts
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)

# POST /analytics endpoint
@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        # Get all records for this region
        records = telemetry.get(region, [])

        if not records:
            result[region] = {
                "avg_latency": None,
                "p95_latency": None,
                "avg_uptime": None,
                "breaches": 0,
            }
            continue

        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        # Mean latency and uptime
        avg_latency = statistics.mean(latencies)
        avg_uptime = statistics.mean(uptimes)

        # 95th percentile latency
        p95_latency = statistics.quantiles(latencies, n=100)[94]  # index 94 = 95th percentile

        # Breaches above threshold
        breaches = sum(1 for x in latencies if x > threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result


@app.get("/")
def read_root():
    return {"message": "FastAPI analytics endpoint is live"}

