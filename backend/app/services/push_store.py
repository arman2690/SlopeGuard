import json
import os
from pathlib import Path
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parents[2] / "data"
DATA_FILE = DATA_DIR / "push_subscriptions.json"


def _ensure_dir():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not DATA_FILE.exists():
        DATA_FILE.write_text("[]", encoding="utf-8")


def load_subscriptions() -> list[dict]:
    _ensure_dir()
    try:
        content = DATA_FILE.read_text(encoding="utf-8")
        subs = json.loads(content)
        if isinstance(subs, list):
            return subs
        return []
    except Exception as e:
        logger.warning(f"Failed to load push subscriptions: {e}")
        return []


def save_subscription(sub_data: dict) -> list[dict]:
    _ensure_dir()
    subs = load_subscriptions()
    endpoint = sub_data.get("endpoint")
    if not endpoint:
        return subs

    # Check if already exists; if so, update keys and device info
    updated = False
    for i, s in enumerate(subs):
        if s.get("endpoint") == endpoint:
            subs[i].update(sub_data)
            subs[i]["last_seen"] = datetime.now(timezone.utc).isoformat()
            updated = True
            break

    if not updated:
        if "created_at" not in sub_data:
            sub_data["created_at"] = datetime.now(timezone.utc).isoformat()
        subs.append(sub_data)

    try:
        temp_file = DATA_FILE.with_suffix(".tmp")
        temp_file.write_text(json.dumps(subs, indent=2), encoding="utf-8")
        temp_file.replace(DATA_FILE)
    except Exception as e:
        logger.error(f"Failed to save push subscription to disk: {e}")

    return subs


def remove_subscription(endpoint: str) -> list[dict]:
    _ensure_dir()
    subs = load_subscriptions()
    original_len = len(subs)
    subs = [s for s in subs if s.get("endpoint") != endpoint]
    if len(subs) != original_len:
        try:
            temp_file = DATA_FILE.with_suffix(".tmp")
            temp_file.write_text(json.dumps(subs, indent=2), encoding="utf-8")
            temp_file.replace(DATA_FILE)
            logger.info(f"Removed expired push subscription: {endpoint[:30]}...")
        except Exception as e:
            logger.error(f"Failed to remove subscription from disk: {e}")
    return subs


def count_subscriptions() -> dict:
    subs = load_subscriptions()
    phones = sum(1 for s in subs if "phone" in s.get("device", "").lower() or "mobile" in s.get("device", "").lower())
    desktops = sum(1 for s in subs if "desktop" in s.get("device", "").lower())
    others = len(subs) - (phones + desktops)
    return {
        "total": len(subs),
        "phones": phones,
        "desktops": desktops,
        "other": others,
    }
