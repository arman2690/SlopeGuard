"""
ISRO environmental / soil-moisture data adapter.

This is an interface stub: it defines the contract the rest of the app
relies on (`is_configured`, `get_soil_moisture`) so a real ISRO data feed
can be dropped in later without touching any calling code. Until
ISRO_API_KEY is set, it reports NOT_CONFIGURED and callers should use
demo data instead.
"""
from ..services import config


def is_configured() -> bool:
    return bool(config.ISRO_API_KEY)


def status() -> str:
    return "DEMO MODE" if not is_configured() else "CONNECTED"


async def get_soil_moisture(lat: float, lon: float) -> dict:
    if not is_configured():
        raise NotImplementedError(
            "ISRO adapter not configured. Set ISRO_API_KEY and implement the "
            "real request in data_sources/isro.py."
        )
    # Real integration point: call the ISRO data endpoint here once access
    # is granted, and map the response into the same shape as the demo
    # data used elsewhere in the app.
    raise NotImplementedError("ISRO live integration not yet implemented.")
