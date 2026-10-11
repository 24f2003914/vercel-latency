import json
import math
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

DATA_FILE = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"

with open(DATA_FILE, "r", encoding="utf-8") as f:
    DATA = json.load(f)


class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: float = 180


@app.post("/")
@app.post("/api/latency")
def calculate_latency(request: LatencyRequest):
    result = {}

    for region in request.regions:
        records = [
            row for row in DATA
            if row["region"] == region
        ]

        if not records:
            continue

        latencies = sorted(
            float(row["latency_ms"]) for row in records
        )
        n = len(latencies)
        p95_index = max(0, math.ceil(0.95 * n) - 1)

        result[region] = {
            "avg_latency": sum(latencies) / n,
            "p95_latency": latencies[p95_index],
            "avg_uptime": sum(
                float(row["uptime_pct"]) for row in records
            ) / n,
            "breaches": sum(
                value > request.threshold_ms
                for value in latencies
            ),
        }

    return result
