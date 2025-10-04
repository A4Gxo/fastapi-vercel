from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import os
import json
import numpy as np

app = FastAPI()

# ✅ Enable CORS globally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # Allow any origin
    allow_credentials=True,
    allow_methods=["*"],       # Allow all HTTP methods
    allow_headers=["*"],       # Allow all headers
)

# ✅ Load telemetry data safely
DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        telemetry = json.load(f)
else:
    telemetry = []
    print("⚠️ Warning: q-vercel-latency.json not found. Telemetry will be empty.")


@app.get("/")
def home():
    return {"status": "ok", "message": "FastAPI Vercel Analytics API 🚀"}


# ✅ POST /analytics: process telemetry by region
@app.post("/analytics")
async def analytics(request: Request):
    """
    Example body:
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
        region_data = [r for r in telemetry if r["region"] == region]
        if not region_data:
            continue

        latencies = np.array([r["latency_ms"] for r in region_data])
        uptimes = np.array([r["uptime_pct"] for r in region_data])

        result[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(np.sum(latencies > threshold)),
        }

    return result


# ✅ OPTIONS /analytics: fixes CORS preflight for browsers
@app.options("/analytics")
async def options_analytics():
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

