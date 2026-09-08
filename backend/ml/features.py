"""
Canonical feature definitions for the SlopeGuard landslide risk model.

Every module that touches the model (training, prediction, the API schema)
imports FEATURES from here so the feature order can never drift between
training and inference.
"""

# Order matters — this is the exact column order the model is trained and
# served on.
FEATURES = [
    "rainfall_24h",        # 0-100 normalized rainfall intensity index
    "rainfall_cumulative",  # 0-100 normalized 7-day cumulative rainfall
    "soil_moisture",       # 0-100 normalized volumetric soil moisture
    "slope",                # 0-100 normalized slope gradient
    "elevation",             # 0-100 normalized elevation band
    "ndvi",                  # 0-100 vegetation index (higher = more vegetation = safer)
    "distance_to_road",      # 0-100 normalized distance to nearest road/cut-slope
    "historical_landslide_density",  # 0-100 normalized historical event density
    "temperature",           # 5-40 degrees C
]

# Central, single-source-of-truth risk thresholds. Every part of the system
# (API, ML post-processing, frontend) should treat these as the only place
# that defines the LOW/MODERATE/HIGH/VERY_HIGH cut points.
RISK_THRESHOLDS = {
    "low": 25,       # 0-25
    "moderate": 50,  # 26-50
    "high": 75,      # 51-75
    # anything above `high` is VERY_HIGH
}


def risk_level_for_score(score: float) -> str:
    if score <= RISK_THRESHOLDS["low"]:
        return "LOW"
    if score <= RISK_THRESHOLDS["moderate"]:
        return "MODERATE"
    if score <= RISK_THRESHOLDS["high"]:
        return "HIGH"
    return "VERY_HIGH"
