from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import statistics

# -----------------------------------------------------
# Initialize FastAPI app
# -----------------------------------------------------
app = FastAPI()

# ✅ Enable CORS globally
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # allow all origins
    allow_credentials=False,
    allow_methods=["*"],        # allow all HTTP methods (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],        # allow all headers
)

# -----------------------------------------------------
# Load telemetry data at startup
# -----------------------------------------------------
# The file must be at the root of your repo: /q-vercel-latency.json
DATA_FILE = os.path.join(os.path.dirname(__file__), "..", "q-vercel-latency.json")
DATA_FILE = os.path.abspath(DATA_FILE)

if not os.path.exists(DATA_FILE):
    raise RuntimeError(f"❌ Telemetry file not found at {DATA_FILE}. Make sure it's committed to the repo.")

with open(DATA_FILE, "r") as f:
    telemetry = json.load(f)


# -----------------------------------------------------
# Root endpoint (sanity check)
# -----------------------------------------------------
@app.get("/")
def read_root():
    return {"message": "✅ FastAPI analytics endpoint is live"}


# -----------------------------------------------------
# POST /analytics
# -----------------------------------------------------
@app.post("/analytics")
async def analytics(request: Request):
    """
    Expects JSON body:
    {
      "regions": ["emea", "apac"],
      "threshold_ms": 180
    }
    Returns per-region metrics: avg_latency, p95_latency, avg_uptime, breaches
    """
    body = await request.json()
    regions = body.get("regions", [])
    threshold_ms = body.get("threshold_ms", 180)

    result = {}

    for region in regions:
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

        # Mean latency & uptime
        avg_latency = statistics.mean(latencies)
        avg_uptime = statistics.mean(uptimes)

        # 95th percentile latency
        p95_latency = statistics.quantiles(latencies, n=100)[94]

        # Breaches count
        breaches = sum(1 for x in latencies if x > threshold_ms)

        result[region] = {
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime": avg_uptime,
            "breaches": breaches,
        }

    return result
