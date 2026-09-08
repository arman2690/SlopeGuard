"""
Bhusanket landslide/geospatial information adapter stub. Only to be wired
up once legally and technically accessible per the data provider's terms.
"""
from ..services import config


def is_configured() -> bool:
    return bool(config.BHUSANKET_API_KEY)


def status() -> str:
    return "NOT CONFIGURED" if not is_configured() else "CONNECTED"


async def get_landslide_inventory(state: str) -> dict:
    if not is_configured():
        raise NotImplementedError(
            "Bhusanket adapter not configured. Set BHUSANKET_API_KEY and "
            "implement the real request in data_sources/bhusanket.py, "
            "respecting the provider's access terms."
        )
    raise NotImplementedError("Bhusanket live integration not yet implemented.")
