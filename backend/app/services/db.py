"""
Thin Supabase wrapper. If SUPABASE_URL / SUPABASE_KEY are not set, every
function here returns None and callers fall back to demo/in-memory data.
This keeps the whole API runnable with zero external services configured.
"""
from . import config

_client = None
_import_failed = False

if config.supabase_configured():
    try:
        from supabase import create_client
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    except Exception:
        _import_failed = True
        _client = None


def get_client():
    return _client


def is_connected() -> bool:
    return _client is not None


def insert_prediction(record: dict):
    if not _client:
        return None
    try:
        return _client.table("risk_predictions").insert(record).execute()
    except Exception:
        return None


def fetch_alerts(limit: int = 50):
    if not _client:
        return None
    try:
        res = _client.table("alerts").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception:
        return None


def insert_alert(record: dict):
    if not _client:
        return None
    try:
        return _client.table("alerts").insert(record).execute()
    except Exception:
        return None


def fetch_risk_zones():
    if not _client:
        return None
    try:
        res = _client.table("risk_zones").select("*").execute()
        return res.data
    except Exception:
        return None
