from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import os
import numpy as np
from typing import Dict, Any

app = FastAPI()

# ✅ Enable CORS for any origin (required for Vercel tests)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load the telemetry JSON file on startup
FILE_PATH = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
with open(FILE_PATH, "r") as f:
    TELEMETRY = json.load(f)


@app.get("/")
def home():
    return {"message": "FastAPI Vercel Analytics is running ✅"}


@app.post("/analytics")
async def analytics(request: Request) -> Dict[str, Any]:
    """
    Example POST body:
    {
        "regions": ["emea", "apac"],
        "threshold_ms": 156
    }
    """
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 0)

    response = {}

    for region in regions:
        # Filter records by region
        records = [r for r in TELEMETRY if r["region"] == region]
        if not records:
            continue

        # Extract latencies and uptimes
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        # Compute metrics
        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = sum(1 for r in records if r["latency_ms"] > threshold_ms)

        response[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return response
