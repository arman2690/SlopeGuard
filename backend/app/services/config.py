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

VAPID_PUBLIC_KEY = os.getenv("VAPID_PUBLIC_KEY", "BAeBCvTGZqeV1HD_M31JZTxcGn44OOVQmAQpJd748xuocoRLI4higIb82Rz-gpK985qCLi2_GVSyDqi5NhP39bQ")
VAPID_PRIVATE_KEY = os.getenv("VAPID_PRIVATE_KEY", "96mKJHE40ozkA7qw0y6jcJziTfs0VcUs9jJdUlDJbDE")
VAPID_CLAIMS_EMAIL = os.getenv("VAPID_CLAIMS_EMAIL", "mailto:admin@slopeguard.in")

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:5500").split(",")
if "https://slope-guard-rust.vercel.app" not in CORS_ORIGINS:
    CORS_ORIGINS.append("https://slope-guard-rust.vercel.app")


def data_mode() -> str:
    return "demo" if DEMO_MODE or not SUPABASE_URL else "live"


def supabase_configured() -> bool:
    return bool(SUPABASE_URL and SUPABASE_KEY)
