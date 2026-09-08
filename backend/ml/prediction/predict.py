"""
Loads the trained XGBoost model and produces explainable risk predictions.

Explainability uses XGBoost's built-in SHAP-style additive feature
contributions (`pred_contribs=True`), which are exact for tree ensembles and
require no extra dependency beyond xgboost itself.
"""
import json
import sys
from pathlib import Path

import numpy as np
import xgboost as xgb

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from ml.features import FEATURES, risk_level_for_score  # noqa: E402

MODEL_DIR = Path(__file__).resolve().parents[1] / "model"
MODEL_PATH = MODEL_DIR / "landslide_xgb_v1.json"
META_PATH = MODEL_DIR / "model_meta.json"

_booster = None
_meta = None


def _load():
    global _booster, _meta
    if _booster is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                "Model not found. Run `python -m backend.ml.training.train` first."
            )
        _booster = xgb.XGBRegressor()
        _booster.load_model(MODEL_PATH)
        with open(META_PATH) as f:
            _meta = json.load(f)
    return _booster, _meta


def model_info() -> dict:
    _, meta = _load()
    return meta


def predict_risk(features: dict) -> dict:
    """
    features: dict with keys matching ml.features.FEATURES (missing keys
    default to a neutral mid-range value so the endpoint is forgiving of
    partial input during prototyping).
    """
    model, meta = _load()

    row = [features.get(f, 50.0 if f != "temperature" else 22.0) for f in FEATURES]
    X = np.array([row], dtype=float)

    raw_score = float(model.predict(X)[0])
    score = float(np.clip(raw_score, 0, 100))
    level = risk_level_for_score(score)

    # Exact additive SHAP contributions from the booster.
    booster = model.get_booster()
    dmat = xgb.DMatrix(X, feature_names=FEATURES)
    contribs = booster.predict(dmat, pred_contribs=True)[0]  # len = n_features + 1 (bias)
    contrib_map = {FEATURES[i]: float(contribs[i]) for i in range(len(FEATURES))}
    bias = float(contribs[-1])

    # Confidence heuristic: distance from the nearest threshold boundary,
    # scaled into a 60-97% band. This is a prototype heuristic, not a
    # calibrated predictive-interval estimate.
    boundaries = [25, 50, 75]
    min_dist = min(abs(score - b) for b in boundaries)
    confidence = float(min(97, round(62 + min_dist * 0.55, 1)))

    recommendations = {
        "LOW": "Conditions are within normal range. Continue routine monitoring; no special action required.",
        "MODERATE": "Increase monitoring frequency in this zone and track rainfall accumulation over the next 24-48 hours.",
        "HIGH": "Notify local disaster management authorities. Restrict non-essential movement on steep sections and inspect drainage.",
        "VERY_HIGH": "Issue an early warning to nearby residents, consider precautionary evacuation of vulnerable structures, and dispatch a field inspection team immediately.",
    }

    return {
        "risk_score": round(score, 1),
        "risk_level": level,
        "confidence": confidence,
        "factors": {k: round(v, 3) for k, v in contrib_map.items()},
        "bias_term": round(bias, 3),
        "recommendation": recommendations[level],
        "model_version": meta["model_version"],
    }


if __name__ == "__main__":
    sample = {
        "rainfall_24h": 82, "rainfall_cumulative": 74, "soil_moisture": 70,
        "slope": 68, "elevation": 55, "ndvi": 30, "distance_to_road": 20,
        "historical_landslide_density": 65, "temperature": 21,
    }
    print(json.dumps(predict_risk(sample), indent=2))
