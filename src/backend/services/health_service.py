"""Service layer for health checks and service diagnostic reporting."""

from datetime import datetime
from typing import Any, Dict
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from src.backend.config import settings
from src.backend.db.models import (
    Account,
    Complaint,
    Location,
    Transaction,
    CashoutEvent,
)
from src.backend.schemas import HealthResponse


class HealthService:
    """System diagnostic and database connectivity monitoring."""

    @staticmethod
    def get_health(db: Session) -> HealthResponse:
        """Evaluates database connectivity, record counts, and ML model subsystem status."""
        db_connected = False
        table_counts: Dict[str, int] = {}

        try:
            db.execute(text("SELECT 1"))
            db_connected = True

            table_counts["locations"] = db.query(func.count(Location.location_id)).scalar() or 0
            table_counts["accounts"] = db.query(func.count(Account.account_id)).scalar() or 0
            table_counts["complaints"] = db.query(func.count(Complaint.case_id)).scalar() or 0
            table_counts["transactions"] = db.query(func.count(Transaction.transaction_id)).scalar() or 0
            table_counts["cashout_events"] = db.query(func.count(CashoutEvent.cashout_event_id)).scalar() or 0
        except Exception:
            db_connected = False

        status = "healthy" if db_connected else "degraded"

        models_status = {
            "model_a_occurrence": "approved_active",
            "model_b_ranking": "fallback_distance_baseline",
            "model_c_timing": "experimental_baseline",
        }

        return HealthResponse(
            status=status,
            timestamp=datetime.utcnow(),
            version=settings.PROJECT_VERSION,
            database_connected=db_connected,
            simulation_mode=settings.SIMULATION_MODE,
            models_status=models_status,
            table_counts=table_counts,
        )
