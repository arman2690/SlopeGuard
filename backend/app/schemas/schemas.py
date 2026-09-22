from typing import Optional, Literal
from pydantic import BaseModel, Field

RiskLevel = Literal["LOW", "MODERATE", "HIGH", "VERY_HIGH"]
AlertSeverity = Literal["Advisory", "Watch", "Warning", "Critical"]


class PredictRequest(BaseModel):
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: float
    longitude: float
    rainfall_24h: float = Field(ge=0, le=100)
    rainfall_cumulative: float = Field(ge=0, le=100)
    soil_moisture: float = Field(ge=0, le=100)
    slope: float = Field(ge=0, le=100)
    elevation: float = Field(ge=0, le=100)
    ndvi: float = Field(ge=0, le=100)
    distance_to_road: float = Field(ge=0, le=100, default=50)
    historical_landslide_density: float = Field(ge=0, le=100, default=30)
    temperature: float = Field(ge=-10, le=50, default=22)


class PredictResponse(BaseModel):
    risk_score: float
    risk_level: RiskLevel
    confidence: float
    factors: dict
    recommendation: str
    model_version: str
    data_mode: str  # "live" | "demo"


class RiskZone(BaseModel):
    id: str
    state: str
    district: str
    latitude: float
    longitude: float
    risk_score: float
    risk_level: RiskLevel
    confidence: float
    rainfall: float
    soil_moisture: float
    slope: float
    elevation: float
    ndvi: float
    historical_landslide_density: float
    timestamp: str
    model_version: str


class WeatherResponse(BaseModel):
    latitude: float
    longitude: float
    rainfall_mm: float
    temperature_c: float
    humidity_pct: float
    wind_kmh: float
    forecast_note: str
    data_mode: str


class Alert(BaseModel):
    id: str
    severity: AlertSeverity
    title: str
    description: str
    state: str
    district: str
    risk_score: float
    created_at: str
    data_mode: str


class AlertCreate(BaseModel):
    severity: AlertSeverity
    title: str
    description: str
    state: str
    district: str
    risk_score: float


class DataSourceStatus(BaseModel):
    name: str
    type: str
    purpose: str
    update_frequency: str
    status: Literal["CONNECTED", "AVAILABLE", "DEMO MODE", "NOT CONFIGURED"]

class SmsAlertRequest(BaseModel):
    phone_number: str
    message: str


class SubscribeRequest(BaseModel):
    phone_number: str

class BlastRequest(BaseModel):
    message: str
    emails: list[str] = []


class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str


class PushSubscription(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys
