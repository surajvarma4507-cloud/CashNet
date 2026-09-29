"""Unit and integration tests for ML Prediction Service and Investigator Decision Support (Stage 3)."""

from datetime import datetime, timedelta
from decimal import Decimal
import uuid

import pytest
from fastapi.testclient import TestClient

from src.backend.config import settings
from src.backend.db.models import (
    Account,
    CashoutEvent,
    Complaint,
    Location,
    LocationCandidate,
    PredictionGroundTruth,
    PredictionRecord,
    PredictionSnapshot,
    Transaction,
)
from src.backend.db.session import SessionLocal
from src.backend.main import app
from src.backend.services.prediction_service import PredictionService

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# 1. Model Artifact and Manifest Tests
# =====================================================================

def test_model_loading_and_feature_manifest():
    """Verify Model A, Model C, and the feature manifest load cleanly with 26 features."""
    manifest = PredictionService.get_feature_manifest()
    assert "model_a_occurrence" in manifest
    features = manifest["model_a_occurrence"]["features"]
    assert len(features) == 26
    assert "complaint_delay_minutes" in features
    assert "estimated_remaining_amount" in features
    assert "max_transaction_amount" in features

    model_a = PredictionService.get_model_a()
    assert model_a is not None
    assert hasattr(model_a, "predict_proba")

    model_c = PredictionService.get_model_c()
    assert model_c is not None
    assert hasattr(model_c, "predict")


# =====================================================================
# 2. Trigger Prediction and Verification of All Subsystems
# =====================================================================

def test_trigger_prediction_on_existing_case(db_session):
    """Verify triggering an end-to-end prediction run on an existing database case."""
    complaint = db_session.query(Complaint).first()
    assert complaint is not None
    case_id = complaint.case_id

    res = client.post(
        f"{settings.API_V1_PREFIX}/cases/{case_id}/predictions",
        json={
            "candidate_count": 5,
            "classification_threshold": 0.5,
            "disclose_provenance": True,
        },
    )
    assert res.status_code == 201
    data = res.json()

    # Core Identifiers
    assert "prediction_id" in data
    assert data["prediction_id"].startswith("PRED_")
    assert data["case_id"] == case_id
    assert "account_id" in data

    # Model A: Occurrence
    occ = data["occurrence"]
    assert 0.0 <= occ["probability_future_cashout"] <= 1.0
    assert isinstance(occ["predicted_has_future_cashout"], bool)
    assert occ["risk_tier"] in ("low", "moderate", "high", "critical")
    assert occ["model_name"] == "occurrence_baseline"
    assert occ["model_status"] == "approved_active"

    # Model B: Candidate Ranking (Fallback Distance Baseline)
    ranking = data["location_ranking"]
    assert ranking["strategy_used"] == "fallback_distance_baseline"
    assert ranking["ml_ranker_status"] == "REJECTED_SYNTHETIC_CANDIDATE_ARTIFACT"
    assert "synthetic candidate injection artifact" in ranking["status_rationale"].lower()
    assert len(ranking["candidates"]) <= 5
    if len(ranking["candidates"]) > 1:
        # Verify strictly sorted by distance ascending
        for i in range(len(ranking["candidates"]) - 1):
            assert ranking["candidates"][i]["distance_from_account_km"] <= ranking["candidates"][i + 1]["distance_from_account_km"]
            assert ranking["candidates"][i]["rank"] == i + 1

    # Model C: Timing Baseline
    timing = data["timing"]
    assert timing["estimated_minutes_until_cashout"] is not None
    assert timing["estimated_minutes_until_cashout"] > 0
    assert timing["timing_window_low_minutes"] <= timing["timing_window_high_minutes"]
    assert timing["variance_status"] == "high_uncertainty_experimental"
    assert "disclaimer" in timing
    assert "experimental" in timing["disclaimer"].lower()

    # Investigator Decision Support Explanation
    explanation = data["explanation"]
    assert len(explanation["summary"]) > 20
    assert isinstance(explanation["risk_factors"], list)
    assert isinstance(explanation["protective_factors"], list)
    assert isinstance(explanation["recommended_actions"], list)
    assert len(explanation["recommended_actions"]) >= 1
    assert "AI-generated advisory assessment" in explanation["advisory_disclaimer"]

    # Provenance
    provenance = data["provenance"]
    assert "occurrence_model" in provenance
    assert "features_used" in provenance
    assert len(provenance["features_used"]) == 26


# =====================================================================
# 3. Snapshot Point-in-Time Prediction
# =====================================================================

def test_prediction_with_specific_snapshot(db_session):
    """Verify that specifying snapshot_id binds feature extraction strictly to that snapshot."""
    snapshot = db_session.query(PredictionSnapshot).first()
    assert snapshot is not None

    res = client.post(
        f"{settings.API_V1_PREFIX}/cases/{snapshot.case_id}/predictions",
        json={
            "snapshot_id": snapshot.snapshot_id,
            "candidate_count": 7,
        },
    )
    assert res.status_code == 201
    data = res.json()

    assert data["snapshot_id"] == snapshot.snapshot_id
    assert data["account_id"] == snapshot.account_id
    # Check that snapshot-derived features match
    features = data["provenance"]["features_used"]
    assert features["complaint_delay_minutes"] == snapshot.complaint_delay_minutes
    assert float(features["total_inflow_24h"]) == float(snapshot.total_inflow_24h)


# =====================================================================
# 4. Prediction Persistence and Retrieval Audit
# =====================================================================

def test_prediction_persistence_and_audit_history(db_session):
    """Verify immutable persistence in PredictionRecord and retrieval via GET endpoints."""
    complaint = db_session.query(Complaint).first()
    case_id = complaint.case_id

    # 1. Trigger prediction
    create_res = client.post(
        f"{settings.API_V1_PREFIX}/cases/{case_id}/predictions",
        json={"candidate_count": 3},
    )
    assert create_res.status_code == 201
    created_data = create_res.json()
    pred_id = created_data["prediction_id"]

    # 2. Retrieve by ID
    get_res = client.get(f"{settings.API_V1_PREFIX}/predictions/{pred_id}")
    assert get_res.status_code == 200
    retrieved_data = get_res.json()

    assert retrieved_data["prediction_id"] == pred_id
    assert retrieved_data["case_id"] == case_id
    assert retrieved_data["occurrence"]["probability_future_cashout"] == created_data["occurrence"]["probability_future_cashout"]
    assert retrieved_data["occurrence"]["risk_tier"] == created_data["occurrence"]["risk_tier"]
    assert len(retrieved_data["location_ranking"]["candidates"]) == len(created_data["location_ranking"]["candidates"])

    # 3. List case predictions
    hist_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/predictions?page=1&page_size=10")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()

    assert hist_data["case_id"] == case_id
    assert hist_data["total_predictions"] >= 1
    pred_ids = [item["prediction_id"] for item in hist_data["items"]]
    assert pred_id in pred_ids


# =====================================================================
# 5. Anti-Leakage & Ground Truth Strict Isolation
# =====================================================================

def test_anti_leakage_ground_truth_isolation(db_session):
    """Verify that future ground-truth cashout events never leak into prediction features."""
    now = datetime(2026, 1, 25, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    acc_id = f"ACC_LEAK_TEST_{uid}"
    case_id = f"CASE_LEAK_TEST_{uid}"
    loc_id = f"LOC_LEAK_TEST_{uid}"

    # Setup isolated test data
    db_session.add(
        Location(
            location_id=loc_id,
            location_name=f"ATM Leak Test {uid}",
            location_type="atm",
            latitude=19.0760,
            longitude=72.8777,
            city="Mumbai",
            region="West",
            area_cluster_id="CLUSTER_TEST",
            synthetic_location_group="test_group",
        )
    )
    db_session.add(
        Account(
            account_id=acc_id,
            account_type="savings",
            account_opened_at=now - timedelta(days=90),
            account_age_days=90,
            synthetic_profile_type="leakage_tester",
        )
    )
    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_id,
            fraud_type="investment_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("50000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Anti-leakage test complaint",
        )
    )

    # Add transaction before prediction timestamp
    tx = Transaction(
        transaction_id=f"TX_LEAK_{uid}",
        case_id=case_id,
        from_account_id=acc_id,
        to_account_id="ACC_MULE_TEST",
        amount=Decimal("50000.00"),
        channel="UPI",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=10),
        completed_at=now + timedelta(minutes=11),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add(tx)

    # Add future ground truth cashout event ONLY
    db_session.add(
        CashoutEvent(
            cashout_event_id=f"CSH_LEAK_{uid}",
            case_id=case_id,
            account_id=acc_id,
            location_id=loc_id,
            transaction_id=f"TX_LEAK_{uid}",
            withdrawal_amount=Decimal("50000.00"),
            cashout_occurred_at=now + timedelta(hours=5),
            is_future_ground_truth=True,  # STRICT GROUND TRUTH
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.commit()

    # Trigger prediction as of complaint registration timestamp
    as_of_ts = (now + timedelta(hours=1)).isoformat()
    res = client.post(
        f"{settings.API_V1_PREFIX}/cases/{case_id}/predictions",
        json={"as_of": as_of_ts},
    )
    assert res.status_code == 201
    data = res.json()

    # Invariant: Ground truth cashout should NOT have been counted in features
    features = data["provenance"]["features_used"]
    assert features["cashout_count"] == 0
    assert features["total_cashout_amount"] == 0.0


# =====================================================================
# 6. Error Handling Tests (404 Not Found)
# =====================================================================

def test_prediction_case_not_found():
    """Verify 404 response for non-existent case ID."""
    res = client.post(f"{settings.API_V1_PREFIX}/cases/NON_EXISTENT_CASE_99999/predictions")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_prediction_snapshot_not_found(db_session):
    """Verify 404 response for non-existent snapshot ID."""
    complaint = db_session.query(Complaint).first()
    case_id = complaint.case_id

    res = client.post(
        f"{settings.API_V1_PREFIX}/cases/{case_id}/predictions",
        json={"snapshot_id": "NON_EXISTENT_SNAP_99999"},
    )
    assert res.status_code == 404
    assert "snapshot" in res.json()["detail"].lower()


def test_prediction_by_id_not_found():
    """Verify 404 response for non-existent prediction ID."""
    res = client.get(f"{settings.API_V1_PREFIX}/predictions/PRED_NONEXISTENT_99999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_list_case_predictions_not_found():
    """Verify 404 response when listing predictions for non-existent case."""
    res = client.get(f"{settings.API_V1_PREFIX}/cases/NON_EXISTENT_CASE_99999/predictions")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()
