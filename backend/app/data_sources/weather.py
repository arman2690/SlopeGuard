"""
Weather adapter. Uses a configured forecast API when WEATHER_API_KEY is set;
otherwise returns clearly-labelled demo data. No key is ever hardcoded.
"""
import random
import httpx
from ..services import config


def is_configured() -> bool:
    return bool(config.WEATHER_API_KEY)


async def get_weather(lat: float, lon: float) -> dict:
    if is_configured():
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(
                    f"{config.WEATHER_API_BASE}/weather",
                    params={"lat": lat, "lon": lon, "appid": config.WEATHER_API_KEY, "units": "metric"},
                )
                resp.raise_for_status()
                data = resp.json()
                return {
                    "latitude": lat,
                    "longitude": lon,
                    "rainfall_mm": data.get("rain", {}).get("1h", 0.0),
                    "temperature_c": data["main"]["temp"],
                    "humidity_pct": data["main"]["humidity"],
                    "wind_kmh": data["wind"]["speed"] * 3.6,
                    "forecast_note": data.get("weather", [{}])[0].get("description", ""),
                    "data_mode": "live",
                }
        except Exception:
            pass  # fall through to demo data on any failure

    # Demo fallback — seeded by coordinates so repeated calls are stable.
    rng = random.Random(round(lat * 1000) + round(lon * 1000))
    return {
        "latitude": lat,
        "longitude": lon,
        "rainfall_mm": round(rng.uniform(5, 140), 1),
        "temperature_c": round(rng.uniform(14, 30), 1),
        "humidity_pct": round(rng.uniform(55, 95), 1),
        "wind_kmh": round(rng.uniform(3, 25), 1),
        "forecast_note": "Demo forecast — configure WEATHER_API_KEY for live data",
        "data_mode": "demo",
    }
