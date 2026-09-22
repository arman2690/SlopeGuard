import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, BackgroundTasks
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pywebpush import webpush, WebPushException

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from ml.prediction import predict as ml_predict  # noqa: E402
from ml.features import FEATURES  # noqa: E402

from ..schemas.schemas import (
    PredictRequest, PredictResponse, RiskZone, WeatherResponse,
    Alert, AlertCreate, DataSourceStatus, PushSubscription
)
from ..services import config, db, demo_data, push_store
from ..data_sources import weather as weather_source
from ..data_sources import isro, bhuvan, bhusanket, earth_engine

router = APIRouter()

# In-memory fallback store for alerts created via POST when no DB is
# connected. Resets on process restart — clearly a demo-mode limitation.
_memory_alerts: list[dict] = []
_memory_push_subscriptions = []


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
def predict(body: PredictRequest, background_tasks: BackgroundTasks):
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

    # AUTOMATED WEB PUSH & EMAIL TRIGGER WHEN HIGH RISK DETECTED
    if result["risk_level"] in ["HIGH", "VERY_HIGH"]:
        auto_msg = f"AUTOMATED EMERGENCY ALERT: {result['risk_level']} landslide risk detected in {body.district or 'Monitored Zone'}, {body.state or 'NE India'} (Score: {result['risk_score']}/100). Immediate evacuation protocols recommended."
        
        # 1. Send Web Push FIRST (ultrafast, parallel direct delivery to phones)
        push_payload = {
            "title": f"🚨 {result['risk_level']} LANDSLIDE RISK ALERT",
            "body": f"Critical slope instability detected in {body.district or 'Monitored Area'}, {body.state or 'NE India'} (Score: {result['risk_score']}/100). Take precautions.",
            "icon": "/icons/icon-192x192.png",
            "badge": "/icons/icon-192x192.png",
            "url": "/"
        }
        background_tasks.add_task(_send_web_push_blast, push_payload)
        
        # 2. Email blast in background
        background_tasks.add_task(_send_emailjs_blast, auto_msg)

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

from ..schemas.schemas import SmsAlertRequest, SubscribeRequest, BlastRequest
import os

_memory_subscribers = []

@router.post("/subscribe")
def subscribe(body: SubscribeRequest):
    contact = body.phone_number.strip()
    if contact not in _memory_subscribers:
        _memory_subscribers.append(contact)
    return {"status": "subscribed", "contact": contact}

def _send_emailjs_blast(message: str, emails: list[str] = None):
    service_id = os.environ.get("EMAILJS_SERVICE_ID", "service_gw9dtvj")
    template_id = os.environ.get("EMAILJS_TEMPLATE_ID", "template_mgrp4za")
    public_key = os.environ.get("EMAILJS_PUBLIC_KEY", "mzMO2sJPbhu54CaIO")

    targets = list(set(_memory_subscribers + (emails or [])))
    if not targets:
        return []

    import urllib.request
    import json

    results = []
    url = 'https://api.emailjs.com/api/v1.0/email/send'

    for email_addr in targets:
        try:
            payload = {
                "service_id": service_id,
                "template_id": template_id,
                "user_id": public_key,
                "template_params": {
                    "to_email": email_addr,
                    "message": message
                }
            }
            req = urllib.request.Request(url, method='POST')
            req.add_header('Content-Type', 'application/json')
            req.add_header('User-Agent', 'Mozilla/5.0')
            data = json.dumps(payload).encode('utf-8')
            
            urllib.request.urlopen(req, data=data, timeout=5)
            results.append({"email": email_addr, "status": "sent"})
        except Exception as e:
            results.append({"email": email_addr, "status": "failed", "error": str(e)})

    return results

def _send_single_push(sub: dict, payload: str, vapid_claims: dict) -> dict:
    endpoint = sub.get("endpoint", "")
    if not endpoint:
        return {"status": "failed", "error": "Missing endpoint"}

    sub_info = {
        "endpoint": endpoint,
        "keys": {
            "p256dh": sub.get("keys", {}).get("p256dh") if isinstance(sub.get("keys"), dict) else None,
            "auth": sub.get("keys", {}).get("auth") if isinstance(sub.get("keys"), dict) else None
        }
    }

    if not sub_info["keys"]["p256dh"] or not sub_info["keys"]["auth"]:
        push_store.remove_subscription(endpoint)
        return {"endpoint": endpoint, "status": "failed", "type": "webpush", "error": "Incomplete encryption keys"}

    try:
        webpush(
            subscription_info=sub_info,
            data=payload,
            vapid_private_key=config.VAPID_PRIVATE_KEY,
            vapid_claims=vapid_claims,
            ttl=86400,
            headers={"Urgency": "high"},
            timeout=5
        )
        return {"endpoint": endpoint, "status": "sent", "type": "webpush", "device": sub.get("device", "Phone")}
    except WebPushException as ex:
        code = getattr(ex.response, "status_code", None) if hasattr(ex, "response") and ex.response is not None else None
        # If subscription expired or was cancelled by user (404/410), evict it permanently
        if code in [404, 410]:
            push_store.remove_subscription(endpoint)
        return {"endpoint": endpoint, "status": "failed", "type": "webpush", "error": str(ex), "code": code}
    except Exception as ex:
        return {"endpoint": endpoint, "status": "failed", "type": "webpush", "error": str(ex)}


def _send_web_push_blast(message):
    if not config.VAPID_PRIVATE_KEY or not config.VAPID_PUBLIC_KEY:
        return []

    vapid_claims = {"sub": config.VAPID_CLAIMS_EMAIL}
    
    subs = []
    if db.is_connected():
        db_subs = db.fetch_push_subscriptions() or []
        for row in db_subs:
            subs.append({
                "endpoint": row["endpoint"],
                "keys": {"p256dh": row["p256dh"], "auth": row["auth"]},
                "device": row.get("user_agent", "Device")
            })
    
    # Merge with persistent disk store (remembers phones permanently)
    stored_subs = push_store.load_subscriptions()
    endpoints_seen = {s["endpoint"] for s in subs}
    for st_sub in stored_subs:
        if st_sub.get("endpoint") not in endpoints_seen:
            subs.append(st_sub)
            endpoints_seen.add(st_sub["endpoint"])

    for mem_sub in _memory_push_subscriptions:
        if mem_sub.get("endpoint") not in endpoints_seen:
            subs.append(mem_sub)
            endpoints_seen.add(mem_sub["endpoint"])
        
    import json
    if isinstance(message, dict):
        payload = json.dumps(message)
    elif isinstance(message, str):
        try:
            parsed = json.loads(message)
            if isinstance(parsed, dict) and "body" in parsed:
                payload = message
            else:
                payload = json.dumps({
                    "title": "🚨 HIGH LANDSLIDE RISK ALERT",
                    "body": message,
                    "icon": "/icons/icon-192x192.png",
                    "badge": "/icons/icon-192x192.png",
                    "url": "/"
                })
        except Exception:
            payload = json.dumps({
                "title": "🚨 HIGH LANDSLIDE RISK ALERT",
                "body": message,
                "icon": "/icons/icon-192x192.png",
                "badge": "/icons/icon-192x192.png",
                "url": "/"
            })
    else:
        payload = json.dumps({"title": "🚨 HIGH LANDSLIDE RISK ALERT", "body": str(message), "icon": "/icons/icon-192x192.png", "url": "/"})
    
    if not subs:
        return []

    # Execute all push dispatches concurrently in parallel (fast delivery!)
    results = []
    max_workers = min(len(subs), 15)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_send_single_push, sub, payload, vapid_claims) for sub in subs]
        for f in as_completed(futures):
            try:
                results.append(f.result())
            except Exception as e:
                results.append({"status": "failed", "error": str(e)})

    return results


@router.post("/dispatch-email-blast")
def dispatch_email_blast(body: BlastRequest):
    # 1. Send Web Push FIRST (ultrafast, parallel, direct to phones)
    push_results = _send_web_push_blast(body.message)
    
    # 2. Send email blast
    email_results = _send_emailjs_blast(body.message, body.emails)
    
    total_results = push_results + email_results
    return {
        "status": "completed",
        "results": total_results,
        "email_count": len(email_results),
        "push_count": len(push_results),
        "message": f"Alert dispatched to {len(push_results)} phone(s)/device(s) and {len(email_results)} email(s)."
    }

@router.get("/notifications/vapidPublicKey")
def vapid_public_key():
    if not config.VAPID_PUBLIC_KEY:
        raise HTTPException(status_code=500, detail="VAPID_PUBLIC_KEY not configured on server.")
    return {"publicKey": config.VAPID_PUBLIC_KEY}


@router.get("/notifications/subscribers-count")
def get_subscribers_count():
    return push_store.count_subscriptions()


@router.post("/notifications/subscribe")
def subscribe_push(body: PushSubscription):
    sub_dict = body.model_dump()
    # Save to persistent disk store (remembers phones permanently)
    push_store.save_subscription(sub_dict)
    
    if sub_dict not in _memory_push_subscriptions:
        _memory_push_subscriptions.append(sub_dict)
    
    if db.is_connected():
        record = {
            "endpoint": body.endpoint,
            "p256dh": body.keys.p256dh,
            "auth": body.keys.auth,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        db.insert_push_subscription(record)
    
    return {"status": "subscribed", "device": body.device}
