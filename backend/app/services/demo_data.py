"""
Synthetic demo dataset — the same 34 NER districts used by the frontend's
offline fallback, but scored here through the real trained XGBoost model so
`/api/risk-zones` demonstrates the live inference pipeline end to end even
when no external GIS/weather feed is connected.

Coordinates are approximate real district locations. Environmental feature
values are synthetic and clearly labelled as demo data everywhere they are
surfaced.
"""
import hashlib
from datetime import datetime, timezone

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ml.prediction.predict import predict_risk  # noqa: E402

DISTRICTS = [
    ("Assam", "Kamrup Metropolitan", 26.1445, 91.7362),
    ("Assam", "Dima Hasao", 25.2168, 93.0142),
    ("Assam", "Karbi Anglong", 25.8330, 93.4370),
    ("Assam", "Cachar", 24.8333, 92.7789),
    ("Assam", "Nagaon", 26.3480, 92.6840),
    ("Assam", "Darrang", 26.4520, 92.0290),
    ("Arunachal Pradesh", "Papum Pare", 27.0844, 93.6053),
    ("Arunachal Pradesh", "West Kameng", 27.2650, 92.4000),
    ("Arunachal Pradesh", "Lower Subansiri", 27.5670, 93.8300),
    ("Arunachal Pradesh", "Upper Siang", 28.7000, 95.1500),
    ("Arunachal Pradesh", "Tawang", 27.5859, 91.8594),
    ("Meghalaya", "East Khasi Hills", 25.5788, 91.8933),
    ("Meghalaya", "West Jaintia Hills", 25.4500, 92.3500),
    ("Meghalaya", "South West Garo Hills", 25.5167, 90.2167),
    ("Meghalaya", "Ri Bhoi", 25.9500, 91.8800),
    ("Meghalaya", "East Garo Hills", 25.5100, 90.6300),
    ("Manipur", "Imphal East", 24.8170, 93.9368),
    ("Manipur", "Churachandpur", 24.3333, 93.6833),
    ("Manipur", "Ukhrul", 25.1167, 94.3667),
    ("Manipur", "Senapati", 25.2667, 94.0167),
    ("Mizoram", "Aizawl", 23.7271, 92.7176),
    ("Mizoram", "Lunglei", 22.8800, 92.7300),
    ("Mizoram", "Champhai", 23.4500, 93.3300),
    ("Mizoram", "Serchhip", 23.3000, 92.8500),
    ("Nagaland", "Kohima", 25.6751, 94.1086),
    ("Nagaland", "Dimapur", 25.9091, 93.7266),
    ("Nagaland", "Phek", 25.6600, 94.4800),
    ("Nagaland", "Wokha", 26.0900, 94.2600),
    ("Tripura", "West Tripura", 23.8315, 91.2868),
    ("Tripura", "Khowai", 24.0667, 91.6000),
    ("Tripura", "Gomati", 23.5300, 91.5300),
    ("Sikkim", "East Sikkim", 27.3389, 88.6065),
    ("Sikkim", "North Sikkim", 27.7167, 88.5833),
    ("Sikkim", "South Sikkim", 27.2333, 88.3500),
]


def _seeded(key: str) -> float:
    h = hashlib.sha256(key.encode()).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def _synthetic_features(state: str, district: str) -> dict:
    bump = 12 if state in ("Sikkim", "Meghalaya", "Arunachal Pradesh") else 0
    r = lambda salt: _seeded(f"{district}-{salt}")  # noqa: E731
    return {
        "rainfall_24h": round(min(100, 30 + r("rain1") * 60 + bump * 0.3), 1),
        "rainfall_cumulative": round(min(100, 25 + r("rain2") * 60), 1),
        "soil_moisture": round(25 + r("soil") * 65, 1),
        "slope": round(min(100, 20 + r("slope") * 70 + bump * 0.4), 1),
        "elevation": round(15 + r("elev") * 70, 1),
        "ndvi": round(35 + r("ndvi") * 55, 1),
        "distance_to_road": round(10 + r("road") * 80, 1),
        "historical_landslide_density": round(min(100, 10 + r("hist") * 70 + bump * 0.3), 1),
        "temperature": round(14 + r("temp") * 16, 1),
    }


def generate_risk_zones() -> list[dict]:
    zones = []
    now = datetime.now(timezone.utc).isoformat()
    for i, (state, district, lat, lon) in enumerate(DISTRICTS):
        features = _synthetic_features(state, district)
        result = predict_risk(features)
        zones.append({
            "id": f"z{i}",
            "state": state,
            "district": district,
            "latitude": lat,
            "longitude": lon,
            "risk_score": result["risk_score"],
            "risk_level": result["risk_level"],
            "confidence": result["confidence"],
            "rainfall": features["rainfall_24h"],
            "soil_moisture": features["soil_moisture"],
            "slope": features["slope"],
            "elevation": features["elevation"],
            "ndvi": features["ndvi"],
            "historical_landslide_density": features["historical_landslide_density"],
            "timestamp": now,
            "model_version": result["model_version"],
        })
    return zones


def generate_alerts(zones: list[dict]) -> list[dict]:
    sev_for = lambda s: (  # noqa: E731
        "Critical" if s >= 80 else "Warning" if s >= 65 else "Watch" if s >= 50 else "Advisory"
    )
    elevated = sorted(
        [z for z in zones if z["risk_score"] >= 45], key=lambda z: -z["risk_score"]
    )[:8]
    alerts = []
    for i, z in enumerate(elevated):
        sev = sev_for(z["risk_score"])
        titles = {
            "Critical": "Very high risk — saturated slope conditions",
            "Warning": "Heavy rainfall accumulation over 24h",
            "Watch": "Elevated slope instability index",
            "Advisory": "Moderate rainfall forecast, monitor conditions",
        }
        alerts.append({
            "id": f"a{i}",
            "severity": sev,
            "title": titles[sev],
            "description": (
                "Demo indicator generated from synthetic rainfall and soil-saturation "
                "data for this location. Verify against official state disaster "
                "management advisories before action."
            ),
            "state": z["state"],
            "district": z["district"],
            "risk_score": z["risk_score"],
            "created_at": z["timestamp"],
            "data_mode": "demo",
        })
    return alerts
