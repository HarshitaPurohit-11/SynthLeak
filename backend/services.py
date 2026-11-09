"""
SynthLeak Alert Generation & Maintenance Workflow Service.
Handles anomaly persistence, alert suppression/cooldown, and ticket generation.
"""

from datetime import datetime, timezone
import uuid
from typing import Optional, List, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select, desc
from backend.models import AlertModel, TicketModel, PipelineModel
from shared.schemas import TicketCreateRequest, TicketResponse, LocationEstimate
from shared.constants import (
    CLASS_PINHOLE_LEAK,
    CLASS_CAVITATION_BURST,
    SEVERITY_NONE,
    SEVERITY_INFO,
    SEVERITY_WARNING,
    SEVERITY_CRITICAL,
    STATUS_OPEN,
)


class AlertService:
    """Manages classification evaluation, severity mapping, and alert database records."""

    @staticmethod
    def evaluate_severity(class_id: int, sound_level_db: float) -> Tuple[bool, str, str]:
        """
        Evaluate alert status and severity level according to CONTRACT.md.
        Returns: (is_alert, severity, message)
        """
        if class_id == CLASS_CAVITATION_BURST:
            return True, SEVERITY_CRITICAL, "Cavitation burst or major pipe breach detected!"
        elif class_id == CLASS_PINHOLE_LEAK:
            if sound_level_db > -35.0:
                return True, SEVERITY_WARNING, "High-intensity pinhole leak detected."
            return True, SEVERITY_INFO, "Developing pinhole orifice acoustic hiss detected."
        else:
            return False, SEVERITY_NONE, "Acoustic signature normal."

    @staticmethod
    def create_alert(
        db: Session,
        pipeline_id: str,
        sensor_id: str,
        class_id: int,
        class_label: str,
        confidence: float,
        dominant_freq: float,
        sound_level_db: float,
        estimated_chainage: Optional[float] = None,
    ) -> Optional[AlertModel]:
        """
        Generate and persist an Alert record if the acoustic event constitutes a leak.
        Prevents redundant alert flooding within a 10-second window on the same pipeline.
        """
        is_alert, severity, _ = AlertService.evaluate_severity(class_id, sound_level_db)
        if not is_alert:
            return None

        # Check for duplicate recent unacknowledged alerts on the same pipeline/class
        recent_alert = db.execute(
            select(AlertModel)
            .where(
                AlertModel.pipeline_id == pipeline_id,
                AlertModel.class_id == class_id,
                AlertModel.is_acknowledged == False,
            )
            .order_by(desc(AlertModel.timestamp))
        ).scalars().first()

        now_iso = datetime.now(timezone.utc).isoformat()
        alert_id = f"ALT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        alert = AlertModel(
            alert_id=alert_id,
            pipeline_id=pipeline_id,
            sensor_id=sensor_id,
            timestamp=now_iso,
            class_id=class_id,
            class_label=class_label,
            confidence=round(confidence, 4),
            dominant_frequency_hz=round(dominant_freq, 1),
            sound_level_db=round(sound_level_db, 2),
            severity=severity,
            estimated_chainage_meters=estimated_chainage,
            is_acknowledged=False,
            ticket_id=None,
        )

        db.add(alert)
        db.commit()
        db.refresh(alert)
        return alert


class TicketService:
    """Manages dispatch and database persistence of maintenance work-order tickets."""

    @staticmethod
    def create_ticket(db: Session, request: TicketCreateRequest) -> TicketResponse:
        """
        Create and persist a new work order ticket based on a validated request.
        Generates canonical ID format: TKT-YYYYMMDD-XXXX
        """
        # Verify pipeline existence
        pipeline = db.execute(
            select(PipelineModel).where(PipelineModel.pipeline_id == request.pipeline_id)
        ).scalars().first()

        if not pipeline:
            raise ValueError(f"Pipeline with ID '{request.pipeline_id}' does not exist.")

        # Check alert existence
        alert = db.execute(
            select(AlertModel).where(AlertModel.alert_id == request.alert_id)
        ).scalars().first()

        now = datetime.now(timezone.utc)
        now_iso = now.isoformat()
        ticket_id = f"TKT-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        loc_dict = request.location_estimate.model_dump() if request.location_estimate else None

        ticket = TicketModel(
            ticket_id=ticket_id,
            alert_id=request.alert_id,
            pipeline_id=request.pipeline_id,
            priority=request.priority,
            status=STATUS_OPEN,
            assigned_crew=request.assigned_crew,
            description=request.description,
            location_estimate=loc_dict,
            created_at=now_iso,
            updated_at=now_iso,
        )

        db.add(ticket)

        # If alert exists, associate ticket with the alert and mark acknowledged
        if alert:
            alert.ticket_id = ticket_id
            alert.is_acknowledged = True

        db.commit()
        db.refresh(ticket)

        return TicketResponse(
            ticket_id=ticket.ticket_id,
            alert_id=ticket.alert_id,
            pipeline_id=ticket.pipeline_id,
            status=ticket.status,
            priority=ticket.priority,
            assigned_crew=ticket.assigned_crew,
            description=ticket.description,
            location_estimate=LocationEstimate.model_validate(ticket.location_estimate) if ticket.location_estimate else None,
            created_at=ticket.created_at,
            updated_at=ticket.updated_at,
        )

