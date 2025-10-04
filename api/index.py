from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import numpy as np
import os

app = FastAPI()

# ✅ Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],          # Allow all HTTP methods including OPTIONS
    allow_headers=["*"],          # Allow all headers
)

# Load telemetry data from q-vercel-latency.json
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")
with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


@app.get("/")
def home():
    return {"status": "ok", "message": "FastAPI Vercel Analytics running 🚀"}


@app.post("/analytics")
async def analytics(request: Request):
    """
    POST body example:
    {
      "regions": ["emea", "apac"],
      "threshold_ms": 156
    }
    """
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
        # Filter telemetry by region
        region_data = [r for r in telemetry if r["region"] == region]
        if not region_data:
            continue

        latencies = np.array([r["latency_ms"] for r in region_data])
        uptimes = np.array([r["uptime_pct"] for r in region_data])

        avg_latency = float(np.mean(latencies))
        p95_latency = float(np.percentile(latencies, 95))
        avg_uptime = float(np.mean(uptimes))
        breaches = int(np.sum(latencies > threshold))

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
