from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import numpy as np
import os

app = FastAPI()

# ✅ Enable CORS globally for POST and OPTIONS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ Load telemetry JSON once at startup
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)

@app.options("/analytics")
async def options_analytics():
    """
    Explicit OPTIONS handler for preflight (not strictly required if CORSMiddleware is set).
    """
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    response_data = {}

    for region in regions:
        region_records = [r for r in telemetry if r["region"] == region]

        if not region_records:
            continue

        latencies = np.array([r["latency_ms"] for r in region_records])
        uptimes = np.array([r["uptime_pct"] for r in region_records])

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(np.sum(latencies > threshold))

        response_data[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches
        }

    # ✅ Ensure CORS headers also on POST response
    response = JSONResponse(content=response_data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response
