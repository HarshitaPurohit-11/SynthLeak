"""
SynthLeak Database Seeding Utility.
Initializes SQLite schema and populates canonical pipelines, sensors, and initial alerts.
"""

import json
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import select
from backend.models import PipelineModel, SensorModel, AlertModel
from backend.database import engine, Base, SessionLocal


def init_db():
    """Create all tables in SQLite."""
    Base.metadata.create_all(bind=engine)


def seed_initial_data(session: Session):
    """Seed pipelines, sensors, and initial alerts if database is unseeded."""
    # Check if pipeline data already exists
    existing = session.execute(select(PipelineModel)).scalars().first()
    if existing:
        return

    examples_dir = Path(__file__).resolve().parent.parent / "shared" / "examples"

    # 1. Seed Pipelines & Sensors from canonical fixture
    pipeline_file = examples_dir / "pipeline_geojson.json"
    if pipeline_file.exists():
        with open(pipeline_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for item in data.get("items", []):
            pipeline = PipelineModel(
                pipeline_id=item["pipeline_id"],
                name=item["name"],
                material=item["material"],
                diameter_mm=item["diameter_mm"],
                length_meters=item["length_meters"],
                status=item["status"],
                geometry=item["geometry"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
            )
            session.add(pipeline)

            for s in item.get("sensors", []):
                sensor = SensorModel(
                    sensor_id=s["sensor_id"],
                    pipeline_id=item["pipeline_id"],
                    chainage_meters=s["chainage_meters"],
                    latitude=s["latitude"],
                    longitude=s["longitude"],
                )
                session.add(sensor)

    # 2. Seed initial Alert from canonical fixture
    alert_file = examples_dir / "alert_response.json"
    if alert_file.exists():
        with open(alert_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        for a in data.get("items", []):
            alert = AlertModel(
                alert_id=a["alert_id"],
                pipeline_id=a["pipeline_id"],
                sensor_id=a["sensor_id"],
                timestamp=a["timestamp"],
                class_id=a["class_id"],
                class_label=a["class_label"],
                confidence=a["confidence"],
                dominant_frequency_hz=a["dominant_frequency_hz"],
                sound_level_db=a["sound_level_db"],
                severity=a["severity"],
                estimated_chainage_meters=a.get("estimated_chainage_meters"),
                is_acknowledged=a.get("is_acknowledged", False),
                ticket_id=a.get("ticket_id"),
            )
            session.add(alert)

    session.commit()


def setup_database():
    """Convenience helper to create tables and seed in one call."""
    init_db()
    with SessionLocal() as session:
        seed_initial_data(session)
