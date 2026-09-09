import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ml.prediction import predict as ml_predict  # noqa: E402
from ml.features import FEATURES  # noqa: E402

from ..schemas.schemas import (
    PredictRequest, PredictResponse, RiskZone, WeatherResponse,
    Alert, AlertCreate, DataSourceStatus,
)
from ..services import config, db, demo_data
from ..data_sources import weather as weather_source
from ..data_sources import isro, bhuvan, bhusanket, earth_engine

router = APIRouter()

# In-memory fallback store for alerts created via POST when no DB is
# connected. Resets on process restart — clearly a demo-mode limitation.
_memory_alerts: list[dict] = []


@router.get("/health")
def health():
    return {
        "status": "ok",
        "demo_mode": config.DEMO_MODE,
        "db_connected": db.is_connected(),
        "db_error": db.connection_error(),
        "time": datetime.now(timezone.utc).isoformat(),
    }


@router.post("/predict", response_model=PredictResponse)
def predict(body: PredictRequest):
    features = {k: getattr(body, k) for k in FEATURES}
    try:
        result = ml_predict.predict_risk(features)
    except FileNotFoundError as e:
        raise HTTPException(status_code=503, detail=str(e))

    record = {
        "latitude": body.latitude,
        "longitude": body.longitude,
        "state": body.state,
        "district": body.district,
        "risk_score": result["risk_score"],
        "risk_level": result["risk_level"],
        "confidence": result["confidence"],
        **features,
        "prediction_timestamp": datetime.now(timezone.utc).isoformat(),
        "model_version": result["model_version"],
    }
    db.insert_prediction(record)  # no-op if DB not connected

    return {**result, "data_mode": config.data_mode()}


@router.get("/risk-zones", response_model=list[RiskZone])
def risk_zones(state: str | None = None):
    zones = db.fetch_risk_zones()
    if zones is None:
        zones = demo_data.generate_risk_zones()
    if state:
        zones = [z for z in zones if z["state"].lower() == state.lower()]
    return zones


@router.get("/risk-zones/{zone_id}", response_model=RiskZone)
def risk_zone_detail(zone_id: str):
    zones = db.fetch_risk_zones() or demo_data.generate_risk_zones()
    for z in zones:
        if z["id"] == zone_id:
            return z
    raise HTTPException(status_code=404, detail="Risk zone not found")


@router.get("/weather/{lat}/{lon}", response_model=WeatherResponse)
async def weather(lat: float, lon: float):
    return await weather_source.get_weather(lat, lon)


@router.get("/alerts", response_model=list[Alert])
def get_alerts(severity: str | None = None):
    stored = db.fetch_alerts()
    if stored is None:
        zones = demo_data.generate_risk_zones()
        stored = demo_data.generate_alerts(zones) + _memory_alerts
    if severity and severity.lower() != "all":
        stored = [a for a in stored if a["severity"].lower() == severity.lower()]
    return stored


@router.post("/alerts", response_model=Alert, status_code=201)
def create_alert(body: AlertCreate):
    record = {
        "id": str(uuid.uuid4()),
        **body.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "data_mode": config.data_mode(),
    }
    saved = db.insert_alert(record)
    if saved is None:
        _memory_alerts.insert(0, record)
    return record


@router.get("/analytics")
def analytics():
    zones = db.fetch_risk_zones() or demo_data.generate_risk_zones()
    dist = {"LOW": 0, "MODERATE": 0, "HIGH": 0, "VERY_HIGH": 0}
    for z in zones:
        dist[z["risk_level"]] += 1

    states = {}
    for z in zones:
        states.setdefault(z["state"], []).append(z["risk_score"])
    state_avg = {s: round(sum(v) / len(v), 1) for s, v in states.items()}

    meta = ml_predict.model_info()

    return {
        "risk_distribution": dist,
        "state_average_risk": state_avg,
        "rainfall_vs_risk": [{"rainfall": z["rainfall"], "risk_score": z["risk_score"]} for z in zones],
        "soil_moisture_vs_risk": [{"soil_moisture": z["soil_moisture"], "risk_score": z["risk_score"]} for z in zones],
        "model_metrics": meta["metrics"],
        "data_mode": config.data_mode(),
    }


@router.get("/locations")
def locations():
    zones = db.fetch_risk_zones() or demo_data.generate_risk_zones()
    return [{"state": z["state"], "district": z["district"], "latitude": z["latitude"], "longitude": z["longitude"]} for z in zones]


@router.get("/data-sources", response_model=list[DataSourceStatus])
def data_sources():
    return [
        {"name": "ISRO", "type": "Environmental / soil-moisture data",
         "purpose": "Soil moisture and terrain indices", "update_frequency": "Daily",
         "status": isro.status()},
        {"name": "Bhuvan", "type": "ISRO geospatial platform",
         "purpose": "Satellite imagery, DEM, land cover", "update_frequency": "Weekly",
         "status": bhuvan.status()},
        {"name": "Bhusanket", "type": "Landslide / geospatial info",
         "purpose": "Landslide inventory reference", "update_frequency": "Periodic",
         "status": bhusanket.status()},
        {"name": "Google Earth Engine", "type": "Satellite processing platform",
         "purpose": "NDVI, rainfall, land cover extraction", "update_frequency": "Daily",
         "status": earth_engine.status()},
        {"name": "Weather Forecast API", "type": "Meteorological data",
         "purpose": "Rainfall, precipitation forecast", "update_frequency": "Hourly",
         "status": "CONNECTED" if weather_source.is_configured() else "DEMO MODE"},
        {"name": "Historical Landslide Records", "type": "Ground-truth event log",
         "purpose": "Model training and validation", "update_frequency": "Static / periodic",
         "status": "AVAILABLE"},
        {"name": "DEM / Terrain Data", "type": "Digital elevation model",
         "purpose": "Slope, aspect, elevation features", "update_frequency": "Static",
         "status": "AVAILABLE"},
    ]


@router.get("/model/info")
def model_info():
    return ml_predict.model_info()
