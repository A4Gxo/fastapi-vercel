from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import os, json, numpy as np

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = os.path.join(os.path.dirname(__file__), "q-vercel-latency.json")

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r") as f:
        telemetry = json.load(f)
else:
    telemetry = []   # 👈 avoid crashing
    print("⚠️ Warning: telemetry file not found. Returning empty data.")

@app.get("/")
def home():
    return {"status": "ok"}

@app.post("/analytics")
async def analytics(request: Request):
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
            "breaches": int(np.sum(latencies > threshold))
        }

    return result
