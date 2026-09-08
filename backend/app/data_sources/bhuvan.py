"""
Bhuvan (ISRO geospatial platform) adapter stub — satellite imagery, DEM,
and land-cover layers. Same pattern as isro.py: reports NOT_CONFIGURED
until BHUVAN_API_KEY is set, so the rest of the app can rely on a stable
interface regardless of whether the real feed is connected.
"""
from ..services import config


def is_configured() -> bool:
    return bool(config.BHUVAN_API_KEY)


def status() -> str:
    return "DEMO MODE" if not is_configured() else "CONNECTED"


async def get_terrain_layer(lat: float, lon: float, radius_km: float = 5.0) -> dict:
    if not is_configured():
        raise NotImplementedError(
            "Bhuvan adapter not configured. Set BHUVAN_API_KEY and implement "
            "the real WMS/WFS request in data_sources/bhuvan.py."
        )
    raise NotImplementedError("Bhuvan live integration not yet implemented.")
