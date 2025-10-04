# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json
import statistics

app = FastAPI()

# ✅ Make sure this is right after app creation
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow all domains
    allow_credentials=False,
    allow_methods=["*"],        # allow GET, POST, OPTIONS, etc.
    allow_headers=["*"],        # allow all headers
)

@app.get("/")
def root():
    return {"message": "Analytics API is running"}

@app.post("/analytics")
async def analytics(request: Request):
    body = await request.json()
    regions = body.get("regions", [])
    threshold = body.get("threshold_ms", 0)

    with open("q-vercel-latency.json", "r") as f:
        telemetry = json.load(f)

    result = {}
    for region in regions:
        records = [r for r in telemetry if r["region"] == region]
        if not records:
            continue
        latencies = [r["latency_ms"] for r in records]
        uptimes = [r["uptime_pct"] for r in records]

        result[region] = {
            "avg_latency": sum(latencies) / len(latencies),
            "p95_latency": statistics.quantiles(latencies, n=100)[94],
            "avg_uptime": sum(uptimes) / len(uptimes),
            "breaches": sum(1 for x in latencies if x > threshold)
        }
    return result

