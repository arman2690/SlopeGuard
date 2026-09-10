import os

DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_API_BASE = os.getenv("WEATHER_API_BASE", "https://api.openweathermap.org/data/2.5")

ISRO_API_KEY = os.getenv("ISRO_API_KEY", "")
BHUVAN_API_KEY = os.getenv("BHUVAN_API_KEY", "")
BHUSANKET_API_KEY = os.getenv("BHUSANKET_API_KEY", "")
GEE_SERVICE_ACCOUNT_JSON = os.getenv("GEE_SERVICE_ACCOUNT_JSON", "")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500,https://slope-guard-rust.vercel.app").split(",")


def data_mode() -> str:
    return "demo" if DEMO_MODE or not SUPABASE_URL else "live"


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)
