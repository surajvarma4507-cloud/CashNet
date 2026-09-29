"""Unit and integration tests for Money-Trail Reconstruction and Graph Topology (Stage 2)."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.backend.config import settings
from src.backend.db.models import (
    Account,
    CashoutEvent,
    Complaint,
    Location,
    PredictionSnapshot,
    Transaction,
)
from src.backend.db.session import SessionLocal
from src.backend.main import app

client = TestClient(app)


# =====================================================================
# Fixtures and Helpers
# =====================================================================

@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# =====================================================================
# Money-Trail Structural & Topology Tests
# =====================================================================

def test_linear_transaction_chain(db_session):
    """Verify linear multi-hop money trail (Victim -> Hop 1 -> Hop 2 -> Hop 3)."""
    now = datetime(2026, 1, 10, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_LIN_{uid}"
    acc_v = f"ACC_LIN_V_{uid}"
    acc_1 = f"ACC_LIN_1_{uid}"
    acc_2 = f"ACC_LIN_2_{uid}"
    acc_3 = f"ACC_LIN_3_{uid}"

    # Setup accounts
    for acc_id in (acc_v, acc_1, acc_2, acc_3):
        acc = Account(
            account_id=acc_id,
            account_type="savings",
            account_opened_at=now - timedelta(days=200),
            account_age_days=200,
            synthetic_profile_type="prototype_tester",
        )
        db_session.add(acc)

    complaint = Complaint(
        case_id=case_id,
        victim_account_id=acc_v,
        fraud_type="investment_scam",
        fraud_channel="UPI",
        fraud_amount=Decimal("50000.00"),
        fraud_occurred_at=now,
        complaint_registered_at=now + timedelta(hours=2),
        complaint_delay_minutes=120,
        synthetic_description="Linear chain synthetic test complaint",
    )
    db_session.add(complaint)

    # 3 linear transactions
    tx1 = Transaction(
        transaction_id=f"TX_LIN_1_{uid}",
        case_id=case_id,
        from_account_id=acc_v,
        to_account_id=acc_1,
        amount=Decimal("50000.00"),
        channel="UPI",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=5),
        completed_at=now + timedelta(minutes=6),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    tx2 = Transaction(
        transaction_id=f"TX_LIN_2_{uid}",
        case_id=case_id,
        from_account_id=acc_1,
        to_account_id=acc_2,
        amount=Decimal("49000.00"),
        channel="IMPS",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=15),
        completed_at=now + timedelta(minutes=16),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    tx3 = Transaction(
        transaction_id=f"TX_LIN_3_{uid}",
        case_id=case_id,
        from_account_id=acc_2,
        to_account_id=acc_3,
        amount=Decimal("48000.00"),
        channel="NEFT",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=30),
        completed_at=now + timedelta(minutes=31),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add_all([tx1, tx2, tx3])
    db_session.commit()

    # Query API
    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case_id
    assert data["victim_account_id"] == acc_v
    assert len(data["ledger"]) == 3

    # Check chronological ordering and hop indexes
    assert data["ledger"][0]["transaction_id"] == tx1.transaction_id
    assert data["ledger"][0]["hop_index"] == 1
    assert data["ledger"][1]["transaction_id"] == tx2.transaction_id
    assert data["ledger"][1]["hop_index"] == 2
    assert data["ledger"][2]["transaction_id"] == tx3.transaction_id
    assert data["ledger"][2]["hop_index"] == 3

    # Check node hop levels and neutral roles
    nodes_by_id = {n["account_id"]: n for n in data["nodes"]}
    assert nodes_by_id[acc_v]["hop_level"] == 0
    assert nodes_by_id[acc_v]["role"] == "source_account"
    assert nodes_by_id[acc_1]["hop_level"] == 1
    assert nodes_by_id[acc_1]["role"] == "intermediary"
    assert nodes_by_id[acc_2]["hop_level"] == 2
    assert nodes_by_id[acc_2]["role"] == "intermediary"
    assert nodes_by_id[acc_3]["hop_level"] == 3
    assert nodes_by_id[acc_3]["role"] == "recipient"

    # Anomalies
    assert data["anomalies"]["has_cycles"] is False
    assert data["anomalies"]["has_missing_links"] is False
    assert data["anomalies"]["max_depth"] == 3
    assert data["anomalies"]["total_hops"] == 3


def test_branched_transaction_flow(db_session):
    """Verify fan-out branching flow (Victim -> [Mule A, Mule B, Mule C])."""
    now = datetime(2026, 1, 11, 12, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_BR_{uid}"
    acc_v = f"ACC_BR_V_{uid}"
    acc_a = f"ACC_BR_A_{uid}"
    acc_b = f"ACC_BR_B_{uid}"
    acc_c = f"ACC_BR_C_{uid}"

    for acc_id in (acc_v, acc_a, acc_b, acc_c):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="current",
                account_opened_at=now - timedelta(days=100),
                account_age_days=100,
                synthetic_profile_type="fanout_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="digital_arrest",
            fraud_channel="UPI",
            fraud_amount=Decimal("150000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Branched fan-out test complaint",
        )
    )

    for i, target_acc in enumerate([acc_a, acc_b, acc_c]):
        db_session.add(
            Transaction(
                transaction_id=f"TX_BR_{i}_{uid}",
                case_id=case_id,
                from_account_id=acc_v,
                to_account_id=target_acc,
                amount=Decimal("50000.00"),
                channel="UPI",
                transaction_type="transfer",
                initiated_at=now + timedelta(minutes=5 + i),
                completed_at=now + timedelta(minutes=6 + i),
                synthetic_event_group_id=f"GRP_{uid}",
            )
        )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["anomalies"]["has_branching"] is True
    assert data["anomalies"]["max_branching_factor"] == 3.0
    assert len(data["ledger"]) == 3

    nodes_by_id = {n["account_id"]: n for n in data["nodes"]}
    assert nodes_by_id[acc_v]["out_degree"] == 3
    assert nodes_by_id[acc_a]["hop_level"] == 1
    assert nodes_by_id[acc_b]["hop_level"] == 1
    assert nodes_by_id[acc_c]["hop_level"] == 1


def test_missing_intermediate_link_detection(db_session):
    """Verify detection of unconnected / island transactions with missing links from source."""
    now = datetime(2026, 1, 12, 14, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_DISC_{uid}"
    acc_v = f"ACC_DISC_V_{uid}"
    acc_1 = f"ACC_DISC_1_{uid}"
    acc_orphan_src = f"ACC_DISC_ORPH_SRC_{uid}"
    acc_orphan_dst = f"ACC_DISC_ORPH_DST_{uid}"

    for acc_id in (acc_v, acc_1, acc_orphan_src, acc_orphan_dst):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=50),
                account_age_days=50,
                synthetic_profile_type="disconnected_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="loan_app_fraud",
            fraud_channel="IMPS",
            fraud_amount=Decimal("30000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Missing link anomaly test case",
        )
    )

    # Connected transfer: Victim -> acc_1
    db_session.add(
        Transaction(
            transaction_id=f"TX_CONN_{uid}",
            case_id=case_id,
            from_account_id=acc_v,
            to_account_id=acc_1,
            amount=Decimal("30000.00"),
            channel="IMPS",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=5),
            completed_at=now + timedelta(minutes=6),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )

    # Disconnected transfer: acc_orphan_src -> acc_orphan_dst
    db_session.add(
        Transaction(
            transaction_id=f"TX_DISC_{uid}",
            case_id=case_id,
            from_account_id=acc_orphan_src,
            to_account_id=acc_orphan_dst,
            amount=Decimal("25000.00"),
            channel="NEFT",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=20),
            completed_at=now + timedelta(minutes=21),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["anomalies"]["has_missing_links"] is True
    assert data["anomalies"]["missing_links_count"] == 2
    assert acc_orphan_src in data["anomalies"]["unconnected_accounts"]
    assert acc_orphan_dst in data["anomalies"]["unconnected_accounts"]

    nodes_by_id = {n["account_id"]: n for n in data["nodes"]}
    assert nodes_by_id[acc_orphan_src]["role"] == "unconnected_node"
    assert nodes_by_id[acc_orphan_src]["hop_level"] == -1


def test_cycle_detection(db_session):
    """Verify detection of cycles in circular money trails (A -> B -> C -> A)."""
    now = datetime(2026, 1, 13, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_CYC_{uid}"
    acc_v = f"ACC_CYC_V_{uid}"
    acc_a = f"ACC_CYC_A_{uid}"
    acc_b = f"ACC_CYC_B_{uid}"
    acc_c = f"ACC_CYC_C_{uid}"

    for acc_id in (acc_v, acc_a, acc_b, acc_c):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="wallet",
                account_opened_at=now - timedelta(days=150),
                account_age_days=150,
                synthetic_profile_type="cycle_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="crypto_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("100000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=3),
            complaint_delay_minutes=180,
            synthetic_description="Cycle detection test complaint",
        )
    )

    # Initial flow: Victim -> A
    # Cycle: A -> B -> C -> A
    tx_list = [
        Transaction(
            transaction_id=f"TX_CYC_0_{uid}",
            case_id=case_id,
            from_account_id=acc_v,
            to_account_id=acc_a,
            amount=Decimal("100000.00"),
            channel="UPI",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=5),
            completed_at=now + timedelta(minutes=6),
            synthetic_event_group_id=f"GRP_{uid}",
        ),
        Transaction(
            transaction_id=f"TX_CYC_1_{uid}",
            case_id=case_id,
            from_account_id=acc_a,
            to_account_id=acc_b,
            amount=Decimal("95000.00"),
            channel="UPI",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=15),
            completed_at=now + timedelta(minutes=16),
            synthetic_event_group_id=f"GRP_{uid}",
        ),
        Transaction(
            transaction_id=f"TX_CYC_2_{uid}",
            case_id=case_id,
            from_account_id=acc_b,
            to_account_id=acc_c,
            amount=Decimal("90000.00"),
            channel="IMPS",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=25),
            completed_at=now + timedelta(minutes=26),
            synthetic_event_group_id=f"GRP_{uid}",
        ),
        Transaction(
            transaction_id=f"TX_CYC_3_{uid}",
            case_id=case_id,
            from_account_id=acc_c,
            to_account_id=acc_a,
            amount=Decimal("85000.00"),
            channel="UPI",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=35),
            completed_at=now + timedelta(minutes=36),
            synthetic_event_group_id=f"GRP_{uid}",
        ),
    ]
    db_session.add_all(tx_list)
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["anomalies"]["has_cycles"] is True
    assert len(data["anomalies"]["cycles"]) >= 1
    # Check that cycle loop contains the cyclic nodes
    cycle_nodes = set()
    for cyc in data["anomalies"]["cycles"]:
        for n in cyc:
            cycle_nodes.add(n)
    assert acc_a in cycle_nodes
    assert acc_b in cycle_nodes
    assert acc_c in cycle_nodes


def test_duplicate_transactions_detection(db_session):
    """Verify duplicate / parallel transactions between the same pair of accounts."""
    now = datetime(2026, 1, 14, 9, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_DUP_{uid}"
    acc_v = f"ACC_DUP_V_{uid}"
    acc_1 = f"ACC_DUP_1_{uid}"

    for acc_id in (acc_v, acc_1):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=90),
                account_age_days=90,
                synthetic_profile_type="duplicate_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="upi_fraud",
            fraud_channel="UPI",
            fraud_amount=Decimal("40000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Duplicate edges test case",
        )
    )

    # 3 separate transfers from acc_v to acc_1
    for i in range(3):
        db_session.add(
            Transaction(
                transaction_id=f"TX_DUP_{i}_{uid}",
                case_id=case_id,
                from_account_id=acc_v,
                to_account_id=acc_1,
                amount=Decimal("10000.00"),
                channel="UPI",
                transaction_type="transfer",
                initiated_at=now + timedelta(minutes=5 * (i + 1)),
                completed_at=now + timedelta(minutes=5 * (i + 1) + 1),
                synthetic_event_group_id=f"GRP_{uid}",
            )
        )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["anomalies"]["has_duplicate_edges"] is True
    assert data["anomalies"]["duplicate_edge_count"] == 2
    assert len(data["ledger"]) == 3


def test_no_linked_transactions_case(db_session):
    """Verify money-trail response for a case with zero transactions."""
    now = datetime(2026, 1, 15, 8, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_EMPTY_{uid}"
    acc_v = f"ACC_EMPTY_V_{uid}"

    db_session.add(
        Account(
            account_id=acc_v,
            account_type="savings",
            account_opened_at=now - timedelta(days=400),
            account_age_days=400,
            synthetic_profile_type="empty_tester",
        )
    )
    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="job_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("15000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=2),
            complaint_delay_minutes=120,
            synthetic_description="Zero transaction case",
        )
    )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case_id
    assert data["summary"]["total_transactions"] == 0
    assert len(data["ledger"]) == 0
    assert len(data["nodes"]) == 1
    assert data["nodes"][0]["account_id"] == acc_v
    assert data["nodes"][0]["role"] == "source_account"
    assert data["nodes"][0]["hop_level"] == 0
    assert data["anomalies"]["max_depth"] == 0


def test_as_of_point_in_time_filtering_on_trail(db_session):
    """Verify that money trail strictly excludes transactions initiated after as_of."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=10")
    assert list_res.status_code == 200

    target_case_id = None
    for item in list_res.json()["items"]:
        if item["transaction_count"] and item["transaction_count"] > 1:
            target_case_id = item["case_id"]
            break

    if not target_case_id:
        pytest.skip("No existing multi-transaction case found for as_of test.")

    # Get all transactions
    full_trail_res = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/money-trail")
    assert full_trail_res.status_code == 200
    full_ledger = full_trail_res.json()["ledger"]
    assert len(full_ledger) > 1

    # Pick cutoff timestamp of the first transaction
    cutoff_ts = full_ledger[0]["initiated_at"]

    filtered_res = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/money-trail?as_of={cutoff_ts}")
    assert filtered_res.status_code == 200
    filtered_data = filtered_res.json()

    assert len(filtered_data["ledger"]) <= len(full_ledger)
    for edge in filtered_data["ledger"]:
        assert edge["initiated_at"] <= cutoff_ts


def test_snapshot_id_filtering_on_trail(db_session):
    """Verify money-trail point-in-time reconstruction using snapshot_id."""
    snapshot = db_session.query(PredictionSnapshot).first()
    if not snapshot:
        pytest.skip("No prediction snapshot available in test database.")

    snap_id = snapshot.snapshot_id
    case_id = snapshot.case_id
    snap_ts = snapshot.prediction_timestamp.isoformat()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail?snapshot_id={snap_id}")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case_id
    for edge in data["ledger"]:
        assert edge["initiated_at"] <= snap_ts


def test_ground_truth_isolation_in_money_trail(db_session):
    """Verify that cashouts with is_future_ground_truth=True never appear in money trail."""
    future_cashout = db_session.query(CashoutEvent).filter(CashoutEvent.is_future_ground_truth.is_(True)).first()
    if not future_cashout:
        pytest.skip("No future ground truth cashout event found in test database.")

    case_id = future_cashout.case_id
    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    # Invariant: Future cashout amount must not inflate summary
    assert "actual_next_location_id" not in data
    assert "prediction_ground_truth" not in data


def test_case_graph_endpoint(db_session):
    """Verify GET /api/v1/cases/{case_id}/graph contract and graph topological metrics."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    target_case_id = list_res.json()["items"][0]["case_id"]

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/graph")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == target_case_id
    assert "nodes" in data
    assert "edges" in data
    assert "metrics" in data

    metrics = data["metrics"]
    assert "node_count" in metrics
    assert "edge_count" in metrics
    assert "density" in metrics
    assert "max_depth" in metrics
    assert "has_cycles" in metrics
    assert "connected_components_count" in metrics
    assert metrics["connected_components_count"] >= 1


def test_money_trail_not_found():
    """Verify 404 response for invalid case ID."""
    res = client.get(f"{settings.API_V1_PREFIX}/cases/INVALID_CASE_XYZ_9999/money-trail")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_deterministic_hop_depth_multi_path(db_session):
    """Verify deterministic shortest-path hop depth when multiple paths reach the same account."""
    now = datetime(2026, 1, 16, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_MULTIPATH_{uid}"
    acc_v = f"ACC_MP_V_{uid}"
    acc_a = f"ACC_MP_A_{uid}"
    acc_b = f"ACC_MP_B_{uid}"
    acc_c = f"ACC_MP_C_{uid}"
    acc_d = f"ACC_MP_D_{uid}"
    acc_e = f"ACC_MP_E_{uid}"
    acc_f = f"ACC_MP_F_{uid}"

    for acc_id in (acc_v, acc_a, acc_b, acc_c, acc_d, acc_e, acc_f):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=200),
                account_age_days=200,
                synthetic_profile_type="multipath_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="investment_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("200000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=2),
            complaint_delay_minutes=120,
            synthetic_description="Multi-path shortest-hop test case",
        )
    )

    # Path 1: V -> C (Hop 1 direct shortcut)
    # Path 2: V -> A -> B -> C (Hop 3 long path)
    # Path 3 (Diamond): V -> D -> E (Hop 2) and V -> F -> E (Hop 2)
    tx_specs = [
        # Long path
        (acc_v, acc_a, Decimal("50000.00"), 5),
        (acc_a, acc_b, Decimal("48000.00"), 10),
        (acc_b, acc_c, Decimal("46000.00"), 15),
        # Shortcut
        (acc_v, acc_c, Decimal("50000.00"), 8),
        # Diamond paths
        (acc_v, acc_d, Decimal("50000.00"), 6),
        (acc_d, acc_e, Decimal("45000.00"), 12),
        (acc_v, acc_f, Decimal("50000.00"), 7),
        (acc_f, acc_e, Decimal("45000.00"), 14),
    ]

    for i, (src, dst, amt, offset_min) in enumerate(tx_specs):
        db_session.add(
            Transaction(
                transaction_id=f"TX_MP_{i}_{uid}",
                case_id=case_id,
                from_account_id=src,
                to_account_id=dst,
                amount=amt,
                channel="UPI",
                transaction_type="transfer",
                initiated_at=now + timedelta(minutes=offset_min),
                completed_at=now + timedelta(minutes=offset_min + 1),
                synthetic_event_group_id=f"GRP_{uid}",
            )
        )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    nodes_by_id = {n["account_id"]: n for n in data["nodes"]}
    assert nodes_by_id[acc_v]["hop_level"] == 0
    assert nodes_by_id[acc_a]["hop_level"] == 1
    assert nodes_by_id[acc_b]["hop_level"] == 2
    # C is reached via direct edge V -> C (hop 1) and via V -> A -> B -> C (hop 3)
    # BFS shortest path must assign hop_level == 1
    assert nodes_by_id[acc_c]["hop_level"] == 1
    assert nodes_by_id[acc_d]["hop_level"] == 1
    assert nodes_by_id[acc_f]["hop_level"] == 1
    # E is reached via V -> D -> E (hop 2) and V -> F -> E (hop 2)
    assert nodes_by_id[acc_e]["hop_level"] == 2

    # Verify edge hop indexes correspond to source node hop + 1
    edges_by_tx = {e["transaction_id"]: e for e in data["ledger"]}
    # Edge V -> C: from hop 0 -> hop_index 1
    tx_vc = next(e for e in data["ledger"] if e["from_account_id"] == acc_v and e["to_account_id"] == acc_c)
    assert tx_vc["hop_index"] == 1
    # Edge B -> C: from hop 2 -> hop_index 3
    tx_bc = next(e for e in data["ledger"] if e["from_account_id"] == acc_b and e["to_account_id"] == acc_c)
    assert tx_bc["hop_index"] == 3


def test_multiple_cycles_and_deduplication(db_session):
    """Verify cycle detection captures multiple distinct cycles without emitting duplicate representations."""
    now = datetime(2026, 1, 17, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_id = f"CASE_MULTICYC_{uid}"
    acc_v = f"ACC_MC_V_{uid}"
    # Cycle 1: A -> B -> A
    acc_a = f"ACC_MC_A_{uid}"
    acc_b = f"ACC_MC_B_{uid}"
    # Cycle 2: C -> D -> E -> C
    acc_c = f"ACC_MC_C_{uid}"
    acc_d = f"ACC_MC_D_{uid}"
    acc_e = f"ACC_MC_E_{uid}"

    for acc_id in (acc_v, acc_a, acc_b, acc_c, acc_d, acc_e):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="wallet",
                account_opened_at=now - timedelta(days=100),
                account_age_days=100,
                synthetic_profile_type="multicycle_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_v,
            fraud_type="crypto_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("150000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=2),
            complaint_delay_minutes=120,
            synthetic_description="Multi-cycle deduplication test case",
        )
    )

    tx_specs = [
        # Source to hubs
        (acc_v, acc_a, Decimal("70000.00"), 5),
        (acc_v, acc_c, Decimal("80000.00"), 6),
        # Cycle 1: A -> B -> A
        (acc_a, acc_b, Decimal("65000.00"), 10),
        (acc_b, acc_a, Decimal("60000.00"), 15),
        # Cycle 2: C -> D -> E -> C
        (acc_c, acc_d, Decimal("75000.00"), 20),
        (acc_d, acc_e, Decimal("70000.00"), 25),
        (acc_e, acc_c, Decimal("65000.00"), 30),
    ]

    for i, (src, dst, amt, offset_min) in enumerate(tx_specs):
        db_session.add(
            Transaction(
                transaction_id=f"TX_MC_{i}_{uid}",
                case_id=case_id,
                from_account_id=src,
                to_account_id=dst,
                amount=amt,
                channel="UPI",
                transaction_type="transfer",
                initiated_at=now + timedelta(minutes=offset_min),
                completed_at=now + timedelta(minutes=offset_min + 1),
                synthetic_event_group_id=f"GRP_{uid}",
            )
        )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_id}/money-trail")
    assert res.status_code == 200
    data = res.json()

    assert data["anomalies"]["has_cycles"] is True
    cycles = data["anomalies"]["cycles"]
    # There should be exactly 2 cycles
    assert len(cycles) == 2

    # Verify each cycle is distinct and no duplicate representations exist
    cycle_sets = [frozenset(c[:-1]) for c in cycles]
    assert len(set(cycle_sets)) == 2
    assert frozenset([acc_a, acc_b]) in cycle_sets
    assert frozenset([acc_c, acc_d, acc_e]) in cycle_sets


def test_graph_metrics_topologies(db_session):
    """Verify graph density and connected component calculations across various topologies."""
    now = datetime(2026, 1, 18, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    # 1. Single-node zero-edge topology
    case_empty = f"CASE_GM_EMPTY_{uid}"
    acc_ve = f"ACC_GM_VE_{uid}"
    db_session.add(
        Account(
            account_id=acc_ve,
            account_type="savings",
            account_opened_at=now - timedelta(days=100),
            account_age_days=100,
            synthetic_profile_type="gm_tester",
        )
    )
    db_session.add(
        Complaint(
            case_id=case_empty,
            victim_account_id=acc_ve,
            fraud_type="phishing",
            fraud_channel="UPI",
            fraud_amount=Decimal("10000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="GM single node case",
        )
    )
    db_session.commit()

    res_e = client.get(f"{settings.API_V1_PREFIX}/cases/{case_empty}/graph")
    assert res_e.status_code == 200
    data_e = res_e.json()
    metrics_e = data_e["metrics"]
    assert metrics_e["node_count"] == 1
    assert metrics_e["edge_count"] == 0
    assert metrics_e["density"] == 0.0
    assert metrics_e["connected_components_count"] == 1

    # 2. Disconnected components topology (V -> A and separate X -> Y)
    case_disc = f"CASE_GM_DISC_{uid}"
    acc_vd = f"ACC_GM_VD_{uid}"
    acc_a = f"ACC_GM_A_{uid}"
    acc_x = f"ACC_GM_X_{uid}"
    acc_y = f"ACC_GM_Y_{uid}"

    for acc_id in (acc_vd, acc_a, acc_x, acc_y):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=100),
                account_age_days=100,
                synthetic_profile_type="gm_tester",
            )
        )

    db_session.add(
        Complaint(
            case_id=case_disc,
            victim_account_id=acc_vd,
            fraud_type="phishing",
            fraud_channel="UPI",
            fraud_amount=Decimal("20000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="GM disconnected case",
        )
    )

    db_session.add(
        Transaction(
            transaction_id=f"TX_GMD_1_{uid}",
            case_id=case_disc,
            from_account_id=acc_vd,
            to_account_id=acc_a,
            amount=Decimal("20000.00"),
            channel="UPI",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=5),
            completed_at=now + timedelta(minutes=6),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.add(
        Transaction(
            transaction_id=f"TX_GMD_2_{uid}",
            case_id=case_disc,
            from_account_id=acc_x,
            to_account_id=acc_y,
            amount=Decimal("15000.00"),
            channel="IMPS",
            transaction_type="transfer",
            initiated_at=now + timedelta(minutes=10),
            completed_at=now + timedelta(minutes=11),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.commit()

    res_d = client.get(f"{settings.API_V1_PREFIX}/cases/{case_disc}/graph")
    assert res_d.status_code == 200
    data_d = res_d.json()
    metrics_d = data_d["metrics"]
    assert metrics_d["node_count"] == 4
    assert metrics_d["edge_count"] == 2
    # Density for N=4, E=2 is 2 / (4 * 3) = 2/12 = 0.1667
    assert metrics_d["density"] == round(2 / 12, 4)
    # 2 independent weakly connected components: {V, A} and {X, Y}
    assert metrics_d["connected_components_count"] == 2
