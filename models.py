"""
models.py
This code defines Pydantic models for handling asset and telemetry data.
The models are used to validate and serialize/deserialize data structures.
"""
from pydantic import BaseModel
from typing import List, Tuple
from datetime import datetime

class Asset(BaseModel):
    deviceId: str
    description: str
    state: str

class AssetsResponse(BaseModel):
    totalCount: int
    items: List[Asset]

class Series(BaseModel):
    name: str
    data: List[Tuple[int, float]]  # [timestamp_ms, value]

class TelemetryResponse(BaseModel):
    series: List[Series]

class TelemetryRecord(BaseModel):
    time: datetime
    device_id:    str
    metric_name:  str
    value:        float
