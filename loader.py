"""
loader.py
This module contains functions to load assets and telemetry data from JSON files.
"""
import json
from pathlib import Path
from config import settings
from models import AssetsResponse, TelemetryResponse

def load_assets() -> AssetsResponse:
    """
    """
    assets_file = Path(settings.assets_file)
    with assets_file.open() as f:
        data = json.load(f)
    return AssetsResponse.model_validate(data)

def load_telemetry(device_id: str) -> TelemetryResponse | None:
    """
    """
    telemetry_dir = Path(settings.telemetry_dir)
    path = telemetry_dir / f"{device_id}.json"
    if not path.exists():
        return None
    with path.open() as f:
        data = json.load(f)
    return TelemetryResponse.model_validate(data)
