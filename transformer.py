"""
transformer.py_
This module contains the transform function that converts loaded telemetry data to telemertr record suitable for db
"""
from datetime import datetime, timezone
from models import TelemetryResponse, TelemetryRecord

def transform(device_id: str, telemetry: TelemetryResponse):
    records = []
    for series in telemetry.series:
        for ts_ms, val in series.data:
            dt = datetime.fromtimestamp(ts_ms / 1000, tz=timezone.utc)
            records.append(TelemetryRecord(
                time=dt,
                device_id=device_id,
                metric_name=series.name,
                value=val,
            ))
    return records
