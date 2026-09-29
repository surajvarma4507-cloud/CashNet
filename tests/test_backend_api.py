"""Integration and unit tests for CASHNET backend API endpoints and anti-leakage invariants."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.backend.config import settings
from src.backend.db.base import Base
from src.backend.db.models import (
    Account,
    AccountLabel,
    CashoutEvent,
    Complaint,
    InvestigatorAction,
    Location,
    PredictionGroundTruth,
    PredictionSnapshot,
    Transaction,
)
from src.backend.db.session import SessionLocal, get_db
from src.backend.main import app

client = TestClient(app)


# =====================================================================
# Health and Diagnostics Endpoints
# =====================================================================

def test_health_check_endpoint():
    """Verify GET /health returns 200, healthy status, and table counts."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True
    assert data["simulation_mode"] is True
    assert "version" in data
    assert "table_counts" in data
    assert data["table_counts"]["complaints"] >= 0
    assert data["table_counts"]["locations"] >= 0
    assert data["models_status"]["model_a_occurrence"] == "approved_active"
    assert data["models_status"]["model_b_ranking"] == "fallback_distance_baseline"


def test_api_v1_health_check():
    """Verify GET /api/v1/health also works under the API prefix."""
    response = client.get(f"{settings.API_V1_PREFIX}/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


# =====================================================================
# Case Management Endpoints
# =====================================================================

def test_list_cases_pagination():
    """Test GET /api/v1/cases pagination contract."""
    response = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert len(data["items"]) <= 10
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10
    assert data["pagination"]["total"] >= len(data["items"])


def test_list_cases_filtering_and_sorting():
    """Test filtering by fraud typology, amount range, and sorting order."""
    response = client.get(
        f"{settings.API_V1_PREFIX}/cases?fraud_type=investment_scam&min_amount=10000&order_by=fraud_amount&order_desc=true"
    )
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["fraud_type"] == "investment_scam"
        assert float(item["fraud_amount"]) >= 10000.0


def test_list_cases_search():
    """Test free-text search across cases."""
    # First get a known case ID
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    assert list_res.status_code == 200
    target_case_id = list_res.json()["items"][0]["case_id"]

    # Search for that exact case ID
    search_res = client.get(f"{settings.API_V1_PREFIX}/cases?search={target_case_id}")
    assert search_res.status_code == 200
    search_data = search_res.json()
    assert len(search_data["items"]) >= 1
    assert any(item["case_id"] == target_case_id for item in search_data["items"])


def test_get_case_detail_found():
    """Test GET /api/v1/cases/{case_id} returns enriched case details."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    target_case_id = list_res.json()["items"][0]["case_id"]

    response = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == target_case_id
    assert "fraud_amount" in data
    assert "victim_account" in data
    assert data["victim_account"]["account_id"] == data["victim_account_id"]
    assert "total_transactions_count" in data
    assert "total_accounts_involved" in data


def test_get_case_detail_not_found():
    """Test GET /api/v1/cases/{case_id} returns 404 for non-existent ID."""
    response = client.get(f"{settings.API_V1_PREFIX}/cases/NON_EXISTENT_CASE_999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# =====================================================================
# Case Transactions and Money Trail
# =====================================================================

def test_get_case_transactions():
    """Test GET /api/v1/cases/{case_id}/transactions returns money trail in order."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=5")
    target_case_id = list_res.json()["items"][0]["case_id"]

    response = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/transactions")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == target_case_id
    assert "items" in data
    assert "total_transactions" in data
    assert len(data["items"]) == data["total_transactions"]

    # Verify chronological ordering
    if len(data["items"]) > 1:
        timestamps = [item["initiated_at"] for item in data["items"]]
        assert timestamps == sorted(timestamps)


def test_get_case_transactions_not_found():
    """Test 404 for transactions on non-existent case."""
    response = client.get(f"{settings.API_V1_PREFIX}/cases/INVALID_CASE/transactions")
    assert response.status_code == 404


# =====================================================================
# Case Accounts & Roles
# =====================================================================

def test_get_case_accounts():
    """Test GET /api/v1/cases/{case_id}/accounts categorizes roles."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    target_case = list_res.json()["items"][0]
    target_case_id = target_case["case_id"]
    victim_acc_id = target_case["victim_account_id"]

    response = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/accounts")
    assert response.status_code == 200
    data = response.json()
    assert data["case_id"] == target_case_id
    assert data["victim_account_id"] == victim_acc_id
    assert len(data["accounts"]) >= 1

    # First account should be victim
    victim_item = next(acc for acc in data["accounts"] if acc["account"]["account_id"] == victim_acc_id)
    assert victim_item["role_in_case"] == "victim"


# =====================================================================
# Investigator Audit Actions
# =====================================================================

def test_create_investigator_action():
    """Test POST /api/v1/cases/{case_id}/actions persists audit log."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    target_case_id = list_res.json()["items"][0]["case_id"]

    payload = {
        "action_type": "account_freeze",
        "notes": "Emergency freeze instruction issued to intermediary wallet",
        "performed_by": "unit_test_investigator",
        "action_status": "completed",
    }
    response = client.post(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/actions", json=payload)
    assert response.status_code == 201
    action_data = response.json()
    assert action_data["case_id"] == target_case_id
    assert action_data["action_type"] == "account_freeze"
    assert action_data["performed_by"] == "unit_test_investigator"
    assert action_data["action_id"].startswith("ACT_")

    # Verify action is visible in case details
    case_res = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}")
    assert case_res.status_code == 200
    case_actions = case_res.json()["actions"]
    assert any(act["action_id"] == action_data["action_id"] for act in case_actions)


# =====================================================================
# GIS Locations Endpoints
# =====================================================================

def test_list_locations_pagination():
    """Test GET /api/v1/locations pagination."""
    response = client.get(f"{settings.API_V1_PREFIX}/locations?page=1&page_size=25")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "pagination" in data
    assert len(data["items"]) <= 25
    assert data["pagination"]["page"] == 1


def test_list_locations_spatial_radius():
    """Test GET /api/v1/locations with lat, lon, and radius_km filter."""
    from src.backend.services.location_service import haversine_distance

    # Delhi coordinate search with 30km radius
    center_lat, center_lon = 28.6139, 77.2090
    radius = 30.0
    response = client.get(
        f"{settings.API_V1_PREFIX}/locations?lat={center_lat}&lon={center_lon}&radius_km={radius}&page=1&page_size=50"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) > 0
    # Every returned terminal must be within the specified radius
    for loc in data["items"]:
        dist = haversine_distance(center_lat, center_lon, float(loc["latitude"]), float(loc["longitude"]))
        assert dist <= radius


def test_get_location_found():
    """Test GET /api/v1/locations/{location_id} returns location details."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/locations?page=1&page_size=1")
    target_loc_id = list_res.json()["items"][0]["location_id"]

    response = client.get(f"{settings.API_V1_PREFIX}/locations/{target_loc_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["location_id"] == target_loc_id
    assert "latitude" in data
    assert "longitude" in data


def test_get_location_not_found():
    """Test 404 for invalid location ID."""
    response = client.get(f"{settings.API_V1_PREFIX}/locations/NON_EXISTENT_LOC_9999")
    assert response.status_code == 404


# =====================================================================
# Anti-Leakage Invariants
# =====================================================================

def test_anti_leakage_ground_truth_isolation():
    """Verify evaluation ground truth is strictly isolated from case and transaction endpoints."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=10")
    assert list_res.status_code == 200

    for item in list_res.json()["items"]:
        case_id = item["case_id"]
        # Case detail
        detail_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}")
        assert detail_res.status_code == 200
        case_dict = detail_res.json()

        # Invariant: Ground truth fields must not be present in public case responses
        assert "actual_next_location_id" not in case_dict
        assert "actual_minutes_until_cashout" not in case_dict
        assert "prediction_ground_truth" not in case_dict
        assert "ground_truth" not in case_dict


# =====================================================================
# Temporal as_of Reconstruction & Snapshot Isolation Tests
# =====================================================================

def test_case_temporal_filtering_as_of():
    """Verify cases list respects point-in-time as_of datetime filtering."""
    # List cases sorted ascending by registration
    res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=20&order_by=complaint_registered_at&order_desc=false")
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) >= 5

    cutoff_ts = items[4]["complaint_registered_at"]
    # Request cases with as_of cutoff
    as_of_res = client.get(f"{settings.API_V1_PREFIX}/cases?as_of={cutoff_ts}")
    assert as_of_res.status_code == 200
    as_of_data = as_of_res.json()
    for item in as_of_data["items"]:
        assert item["complaint_registered_at"] <= cutoff_ts


def test_case_transactions_as_of_filtering():
    """Verify /cases/{case_id}/transactions filters out transactions initiated after as_of."""
    db = SessionLocal()
    try:
        # Find a case with multiple transactions
        case_with_multi_tx = (
            db.query(Complaint.case_id)
            .join(Transaction, Complaint.case_id == Transaction.case_id)
            .group_by(Complaint.case_id)
            .having(Transaction.transaction_id != None)  # noqa: E711
            .first()
        )
        assert case_with_multi_tx is not None
        case_id = case_with_multi_tx[0]

        all_tx_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/transactions")
        assert all_tx_res.status_code == 200
        all_txs = all_tx_res.json()["items"]
        assert len(all_txs) > 0

        if len(all_txs) > 1:
            mid_idx = len(all_txs) // 2
            cutoff_ts = all_txs[mid_idx]["initiated_at"]

            filtered_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/transactions?as_of={cutoff_ts}")
            assert filtered_res.status_code == 200
            filtered_data = filtered_res.json()

            assert len(filtered_data["items"]) <= len(all_txs)
            assert len(filtered_data["items"]) > 0
            for tx in filtered_data["items"]:
                assert tx["initiated_at"] <= cutoff_ts
    finally:
        db.close()


def test_case_snapshot_based_point_in_time_reconstruction():
    """Verify prediction-time reconstruction can use prediction snapshot ID."""
    db = SessionLocal()
    try:
        snapshot = db.query(PredictionSnapshot).first()
        assert snapshot is not None
        snap_id = snapshot.snapshot_id
        case_id = snapshot.case_id
        snap_ts = snapshot.prediction_timestamp.isoformat()

        # Reconstruct case details via snapshot_id
        detail_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}?snapshot_id={snap_id}")
        assert detail_res.status_code == 200
        case_data = detail_res.json()
        assert case_data["case_id"] == case_id

        # Reconstruct transactions via snapshot_id
        tx_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/transactions?snapshot_id={snap_id}")
        assert tx_res.status_code == 200
        for tx in tx_res.json()["items"]:
            assert tx["initiated_at"] <= snap_ts

        # Test invalid snapshot ID raises 404
        invalid_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}?snapshot_id=NON_EXISTENT_SNAPSHOT_ID")
        assert invalid_res.status_code == 404
    finally:
        db.close()


def test_future_ground_truth_cashout_exclusion_in_case_dossier():
    """Verify cashouts with is_future_ground_truth=True are strictly excluded from operational case details."""
    db = SessionLocal()
    try:
        future_cashout = db.query(CashoutEvent).filter(CashoutEvent.is_future_ground_truth.is_(True)).first()
        assert future_cashout is not None
        case_id = future_cashout.case_id

        detail_res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}")
        assert detail_res.status_code == 200
        case_data = detail_res.json()

        visible_cashout_ids = {c["cashout_event_id"] for c in case_data["cashouts"]}
        assert future_cashout.cashout_event_id not in visible_cashout_ids
    finally:
        db.close()


def test_investigator_action_immutability_and_append_only():
    """Verify InvestigatorAction is strictly append-only; update/delete operations raise PermissionError."""
    import uuid
    db = SessionLocal()
    try:
        action = InvestigatorAction(
            action_id=f"ACT_TEST_{uuid.uuid4().hex[:8].upper()}",
            case_id=db.query(Complaint.case_id).first()[0],
            action_type="account_freeze",
            notes="Append-only verification test action",
            performed_by="audit_tester",
            action_status="completed",
        )
        db.add(action)
        db.commit()

        # Attempt to modify (UPDATE)
        action.notes = "Attempted tampering of notes"
        with pytest.raises(PermissionError, match="append-only"):
            db.commit()
        db.rollback()

        # Attempt to DELETE
        db.delete(action)
        with pytest.raises(PermissionError, match="append-only"):
            db.commit()
        db.rollback()
    finally:
        db.close()


def test_list_location_clusters():
    """Verify GET /api/v1/locations/clusters returns aggregated clusters with valid centroids and terminal counts."""
    response = client.get("/api/v1/locations/clusters")
    assert response.status_code == 200
    data = response.json()
    assert "total_clusters" in data
    assert "items" in data
    assert data["total_clusters"] > 0
    assert len(data["items"]) == data["total_clusters"]

    first = data["items"][0]
    assert "area_cluster_id" in first
    assert "cluster_name" in first
    assert "city" in first
    assert "region" in first
    assert "center_latitude" in first
    assert "center_longitude" in first
    assert "total_locations" in first
    assert first["total_locations"] > 0
    assert "atm_count" in first
    assert "branch_count" in first
    assert "kiosk_count" in first
    assert "observed_cashout_events_count" in first
    assert "total_observed_cashout_volume" in first

    # City filter test
    city_filter_resp = client.get("/api/v1/locations/clusters?city=Mumbai")
    assert city_filter_resp.status_code == 200
    mumbai_clusters = city_filter_resp.json()
    for cluster in mumbai_clusters["items"]:
        assert "Mumbai" in cluster["city"] or "Maharashtra" in cluster["region"] or "MUM" in cluster["area_cluster_id"]


def test_list_location_hotspots_anti_leakage():
    """Verify GET /api/v1/locations/hotspots aggregates only historical non-ground-truth cashouts."""
    response = client.get("/api/v1/locations/hotspots?limit=10&min_cashouts=1")
    assert response.status_code == 200
    data = response.json()
    assert "total_hotspots" in data
    assert "items" in data
    assert isinstance(data["items"], list)

    for item in data["items"]:
        assert "location_id" in item
        assert "location_name" in item
        assert "location_type" in item
        assert "city" in item
        assert "latitude" in item
        assert "longitude" in item
        assert "observed_cashout_count" in item
        assert item["observed_cashout_count"] >= 1
        assert "total_observed_cashout_volume" in item
        assert "activity_risk_level" in item
        assert item["activity_risk_level"] in ("high", "elevated", "moderate")


