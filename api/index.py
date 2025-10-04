# api/index.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
import json

app = FastAPI()

# Enable CORS for POST requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/analytics")
async def analytics(request: Request):
    """
    POST body:
    {
      "regions": ["emea", "apac"],
      "threshold_ms": 156
    }
    """
    data = await request.json()
    regions = data.get("regions", [])
    threshold = data.get("threshold_ms", 180)

    # Load telemetry bundle (pretend it’s bundled or fetched from file)
    # For the exercise, use a local sample
    with open("q-vercel-latency.json", "r") as f:
        telemetry = json.load(f)

    result = {}
    for region in regions:
        if region not in telemetry:
            continue
        region_data = telemetry[region]
        latencies = np.array([d["latency_ms"] for d in region_data])
        uptimes = np.array([d["uptime"] for d in region_data])

        result[region] = {
            "avg_latency": float(latencies.mean()),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(uptimes.mean()),
            "breaches": int((latencies > threshold).sum()),
        }

    return result

@app.get("/")
def root():
    return {"message": "FastAPI Vercel analytics running"}
