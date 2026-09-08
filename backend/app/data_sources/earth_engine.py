"""
Google Earth Engine adapter stub for NDVI, rainfall, land-cover and terrain
variable extraction. Requires a GEE service account; see
GEE_SERVICE_ACCOUNT_JSON in config.py.
"""
from ..services import config


def is_configured() -> bool:
    return bool(config.GEE_SERVICE_ACCOUNT_JSON)


def status() -> str:
    return "DEMO MODE" if not is_configured() else "CONNECTED"


async def get_ndvi(lat: float, lon: float, date_range: tuple) -> dict:
    if not is_configured():
        raise NotImplementedError(
            "Earth Engine adapter not configured. Set GEE_SERVICE_ACCOUNT_JSON "
            "and implement the ee.Initialize()/image-collection query in "
            "data_sources/earth_engine.py."
        )
    raise NotImplementedError("Earth Engine live integration not yet implemented.")
