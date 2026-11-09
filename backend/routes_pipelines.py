"""
SynthLeak Pipeline Topology & Acoustic Telemetry Endpoints.
Implements GET /pipelines conforming strictly to CONTRACT.md schemas.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.database import get_db
from backend.models import PipelineModel
from shared.schemas import PipelineListResponse, PipelineItem, SensorMetadata, LineStringGeometry

router = APIRouter(tags=["Pipelines"])


@router.get(
    "/pipelines",
    response_model=PipelineListResponse,
    summary="Get All Pipelines & Sensor Arrays",
    description="Returns list of monitored pipeline segments with GeoJSON coordinates and mounted sensor metadata.",
)
def get_pipelines(
    material: Optional[str] = Query(default=None, description="Filter by pipe material (e.g., Cast Iron, PVC)"),
    status: Optional[str] = Query(default=None, description="Filter by operational status (NORMAL, WARNING, CRITICAL)"),
    db: Session = Depends(get_db),
):
    query = select(PipelineModel)
    if material is not None and not isinstance(material, Query):
        query = query.where(PipelineModel.material == material)
    if status is not None and not isinstance(status, Query):
        query = query.where(PipelineModel.status == status)

    results = db.execute(query).scalars().unique().all()

    items = []
    for p in results:
        sensor_items = [
            SensorMetadata(
                sensor_id=s.sensor_id,
                chainage_meters=s.chainage_meters,
                latitude=s.latitude,
                longitude=s.longitude,
            )
            for s in p.sensors
        ]

        items.append(
            PipelineItem(
                pipeline_id=p.pipeline_id,
                name=p.name,
                material=p.material,
                diameter_mm=p.diameter_mm,
                length_meters=p.length_meters,
                status=p.status,
                sensors=sensor_items,
                geometry=LineStringGeometry.model_validate(p.geometry),
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
        )

    return PipelineListResponse(total=len(items), items=items)
