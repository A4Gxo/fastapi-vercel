from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import statistics

app = FastAPI()

# ✅ Enable CORS globally for POST requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load telemetry data once
with open("api/q-vercel-latency.json", "r") as f:
    telemetry_data = json.load(f)

@app.options("/analytics")
async def options_analytics():
    """Handle browser preflight checks."""
    response = JSONResponse(content={})
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    response_data = {}

    for region in regions:
        region_data = [r for r in telemetry_data if r["region"] == region]

        if not region_data:
            continue

        latencies = [r["latency_ms"] for r in region_data]
        uptimes = [r["uptime_pct"] for r in region_data]
        breaches = len([l for l in latencies if l > threshold_ms])

        avg_latency = statistics.mean(latencies)
        p95_latency = statistics.quantiles(latencies, n=100)[94]  # 95th percentile
        avg_uptime = statistics.mean(uptimes)

        response_data[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    response = JSONResponse(content=response_data)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.get("/")
def root():
    return {"message": "Analytics API is running"}
