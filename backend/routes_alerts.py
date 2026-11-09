"""
SynthLeak Acoustic Alert Incident History Endpoints.
Implements GET /alerts conforming strictly to CONTRACT.md schemas.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.database import get_db
from backend.models import AlertModel
from shared.schemas import AlertListResponse, AlertItem

router = APIRouter(tags=["Alerts"])


@router.get(
    "/alerts",
    response_model=AlertListResponse,
    summary="Get Acoustic Detection Alert History",
    description="Returns recorded acoustic leak alerts with filtering by pipeline, severity, and acknowledgment.",
)
def get_alerts(
    pipeline_id: Optional[str] = Query(default=None, description="Filter by pipeline identifier"),
    severity: Optional[str] = Query(default=None, description="Filter by severity: INFO, WARNING, CRITICAL"),
    acknowledged: Optional[bool] = Query(default=None, description="Filter by acknowledgment state"),
    limit: int = Query(default=50, ge=1, le=500, description="Maximum alerts to retrieve"),
    db: Session = Depends(get_db),
):
    query = select(AlertModel)

    if pipeline_id is not None and not isinstance(pipeline_id, Query):
        query = query.where(AlertModel.pipeline_id == pipeline_id)
    if severity is not None and not isinstance(severity, Query):
        query = query.where(AlertModel.severity == severity)
    if acknowledged is not None and not isinstance(acknowledged, Query):
        query = query.where(AlertModel.is_acknowledged == acknowledged)

    limit_val = limit if isinstance(limit, int) else 50
    query = query.order_by(desc(AlertModel.timestamp)).limit(limit_val)
    results = db.execute(query).scalars().all()

    items = [
        AlertItem(
            alert_id=a.alert_id,
            pipeline_id=a.pipeline_id,
            sensor_id=a.sensor_id,
            timestamp=a.timestamp,
            class_id=a.class_id,
            class_label=a.class_label,
            confidence=a.confidence,
            dominant_frequency_hz=a.dominant_frequency_hz,
            sound_level_db=a.sound_level_db,
            severity=a.severity,
            estimated_chainage_meters=a.estimated_chainage_meters,
            is_acknowledged=a.is_acknowledged,
            ticket_id=a.ticket_id,
        )
        for a in results
    ]

    return AlertListResponse(total=len(items), items=items)
