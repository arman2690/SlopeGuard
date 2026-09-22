"""
Thin Supabase wrapper. If SUPABASE_URL / SUPABASE_KEY are not set, every
function here returns None and callers fall back to demo/in-memory data.
This keeps the whole API runnable with zero external services configured.
"""
import traceback
from . import config

_client = None
_last_error = None

if config.supabase_configured():
    try:
        from supabase import create_client
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_KEY)
    except Exception as e:
        _last_error = f"{type(e).__name__}: {e}"
        _client = None
else:
    _last_error = "SUPABASE_URL or SUPABASE_KEY not set"


def get_client():
    return _client


def is_connected() -> bool:
    return _client is not None


def connection_error() -> str | None:
    """Human-readable reason the DB isn't connected, or None if it is."""
    return _last_error


def _record_error(e: Exception):
    global _last_error
    _last_error = f"{type(e).__name__}: {e}"


def insert_prediction(record: dict):
    if not _client:
        return None
    try:
        return _client.table("risk_predictions").insert(record).execute()
    except Exception as e:
        _record_error(e)
        return None


def fetch_alerts(limit: int = 50):
    if not _client:
        return None
    try:
        res = _client.table("alerts").select("*").order("created_at", desc=True).limit(limit).execute()
        return res.data
    except Exception as e:
        _record_error(e)
        return None


def insert_alert(record: dict):
    if not _client:
        return None
    try:
        return _client.table("alerts").insert(record).execute()
    except Exception as e:
        _record_error(e)
        return None


def fetch_risk_zones():
    if not _client:
        return None
    try:
        res = _client.table("risk_zones").select("*").execute()
        return res.data
    except Exception as e:
        _record_error(e)
        return None


def fetch_push_subscriptions():
    if not _client:
        return None
    try:
        res = _client.table("push_subscriptions").select("*").execute()
        return res.data
    except Exception as e:
        _record_error(e)
        return None


def insert_push_subscription(record: dict):
    if not _client:
        return None
    try:
        return _client.table("push_subscriptions").upsert(record, on_conflict="endpoint").execute()
    except Exception as e:
        _record_error(e)
        return None
