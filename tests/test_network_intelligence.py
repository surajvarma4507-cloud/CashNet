"""Unit and integration tests for Cross-Case Network Intelligence and Account Syndicates (Stage 2)."""

import uuid
from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from src.backend.config import settings
from src.backend.db.models import (
    Account,
    CaseRelationship,
    CashoutEvent,
    Complaint,
    Location,
    Transaction,
)
from src.backend.db.session import SessionLocal
from src.backend.main import app

client = TestClient(app)


@pytest.fixture
def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_cross_case_shared_account_network(db_session):
    """Verify that cross-case shared intermediary mule accounts link related cases with evidence."""
    now = datetime(2026, 1, 20, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    case_1 = f"CASE_NET_1_{uid}"
    case_2 = f"CASE_NET_2_{uid}"
    victim_1 = f"ACC_NET_V1_{uid}"
    victim_2 = f"ACC_NET_V2_{uid}"
    shared_mule = f"ACC_NET_SHARED_{uid}"
    recipient_1 = f"ACC_NET_R1_{uid}"
    recipient_2 = f"ACC_NET_R2_{uid}"

    for acc_id in (victim_1, victim_2, shared_mule, recipient_1, recipient_2):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=120),
                account_age_days=120,
                synthetic_profile_type="syndicate_tester",
            )
        )

    # Case 1
    db_session.add(
        Complaint(
            case_id=case_1,
            victim_account_id=victim_1,
            fraud_type="investment_scam",
            fraud_channel="UPI",
            fraud_amount=Decimal("100000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Case 1 with shared syndicate node",
        )
    )
    # Case 2
    db_session.add(
        Complaint(
            case_id=case_2,
            victim_account_id=victim_2,
            fraud_type="job_scam",
            fraud_channel="IMPS",
            fraud_amount=Decimal("80000.00"),
            fraud_occurred_at=now + timedelta(days=1),
            complaint_registered_at=now + timedelta(days=1, hours=2),
            complaint_delay_minutes=120,
            synthetic_description="Case 2 sharing syndicate node with Case 1",
        )
    )

    # Transactions for Case 1
    tx_1a = Transaction(
        transaction_id=f"TX_NET_1A_{uid}",
        case_id=case_1,
        from_account_id=victim_1,
        to_account_id=shared_mule,
        amount=Decimal("100000.00"),
        channel="UPI",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=5),
        completed_at=now + timedelta(minutes=6),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    tx_1b = Transaction(
        transaction_id=f"TX_NET_1B_{uid}",
        case_id=case_1,
        from_account_id=shared_mule,
        to_account_id=recipient_1,
        amount=Decimal("95000.00"),
        channel="UPI",
        transaction_type="transfer",
        initiated_at=now + timedelta(minutes=10),
        completed_at=now + timedelta(minutes=11),
        synthetic_event_group_id=f"GRP_{uid}",
    )

    # Transactions for Case 2
    tx_2a = Transaction(
        transaction_id=f"TX_NET_2A_{uid}",
        case_id=case_2,
        from_account_id=victim_2,
        to_account_id=shared_mule,
        amount=Decimal("80000.00"),
        channel="IMPS",
        transaction_type="transfer",
        initiated_at=now + timedelta(days=1, minutes=5),
        completed_at=now + timedelta(days=1, minutes=6),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    tx_2b = Transaction(
        transaction_id=f"TX_NET_2B_{uid}",
        case_id=case_2,
        from_account_id=shared_mule,
        to_account_id=recipient_2,
        amount=Decimal("78000.00"),
        channel="IMPS",
        transaction_type="transfer",
        initiated_at=now + timedelta(days=1, minutes=15),
        completed_at=now + timedelta(days=1, minutes=16),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add_all([tx_1a, tx_1b, tx_2a, tx_2b])
    db_session.commit()

    # Query network for Case 1
    res = client.get(f"{settings.API_V1_PREFIX}/cases/{case_1}/network")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == case_1
    assert case_2 in data["connected_case_ids"]
    assert data["connected_cases_count"] >= 1
    assert shared_mule in data["direct_shared_accounts"]

    # Verify evidence
    rel = next((r for r in data["relationships"] if r["related_case_id"] == case_2), None)
    assert rel is not None
    assert rel["shared_account_id"] == shared_mule
    assert rel["shared_transaction_count"] >= 2
    assert float(rel["shared_amount_volume"]) >= 158000.0


def test_case_related_cases_pagination(db_session):
    """Test GET /api/v1/cases/{case_id}/related-cases pagination."""
    list_res = client.get(f"{settings.API_V1_PREFIX}/cases?page=1&page_size=1")
    target_case_id = list_res.json()["items"][0]["case_id"]

    res = client.get(f"{settings.API_V1_PREFIX}/cases/{target_case_id}/related-cases?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()

    assert data["case_id"] == target_case_id
    assert "total_related_cases" in data
    assert "items" in data
    assert "pagination" in data
    assert data["pagination"]["page"] == 1
    assert data["pagination"]["page_size"] == 10


def test_account_network_intelligence(db_session):
    """Verify GET /api/v1/accounts/{account_id}/network returns profile, flow totals, and co-occurring accounts."""
    # Find an active account from transactions
    tx = db_session.query(Transaction).first()
    assert tx is not None
    target_acc_id = tx.from_account_id

    res = client.get(f"{settings.API_V1_PREFIX}/accounts/{target_acc_id}/network")
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == target_acc_id
    assert "observed_roles" in data
    assert "participating_cases" in data
    assert "total_inflow_observed" in data
    assert "total_outflow_observed" in data
    assert "total_transactions_count" in data
    assert "co_occurring_accounts" in data
    assert "activity_window" in data
    assert data["total_transactions_count"] >= 1


def test_account_money_trails(db_session):
    """Verify GET /api/v1/accounts/{account_id}/money-trails returns multi-case trail records."""
    tx = db_session.query(Transaction).filter(Transaction.case_id.isnot(None)).first()
    assert tx is not None
    target_acc_id = tx.from_account_id

    res = client.get(f"{settings.API_V1_PREFIX}/accounts/{target_acc_id}/money-trails")
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == target_acc_id
    assert "total_cases" in data
    assert "money_trails" in data
    assert data["total_cases"] >= 1
    for trail in data["money_trails"]:
        assert "case_id" in trail
        assert "role_in_case" in trail
        assert "hop_level" in trail
        assert "total_received_in_case" in trail
        assert "total_sent_in_case" in trail


def test_network_as_of_filtering(db_session):
    """Verify point-in-time as_of filtering on account network endpoint."""
    tx = db_session.query(Transaction).order_by(Transaction.initiated_at.desc()).first()
    assert tx is not None
    target_acc = tx.from_account_id
    cutoff_ts = tx.initiated_at.isoformat()

    res = client.get(f"{settings.API_V1_PREFIX}/accounts/{target_acc}/network?as_of={cutoff_ts}")
    assert res.status_code == 200
    data = res.json()

    assert data["as_of"] is not None
    assert data["as_of"] <= cutoff_ts


def test_account_not_found():
    """Verify 404 response for non-existent account ID."""
    res = client.get(f"{settings.API_V1_PREFIX}/accounts/NON_EXISTENT_ACC_99999/network")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_related_cases_not_found():
    """Verify 404 response for non-existent case ID."""
    res = client.get(f"{settings.API_V1_PREFIX}/cases/NON_EXISTENT_CASE_99999/related-cases")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_account_network_as_of_cashout_isolation(db_session):
    """Verify point-in-time as_of filtering prevents future cashouts from appearing in observed_roles."""
    now = datetime(2026, 1, 22, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    acc_id = f"ACC_CSH_ISO_{uid}"
    case_id = f"CASE_CSH_ISO_{uid}"
    loc_id = f"LOC_CSH_ISO_{uid}"

    from src.backend.db.models import Location
    db_session.add(
        Location(
            location_id=loc_id,
            location_name=f"ATM Hub {uid}",
            location_type="atm",
            latitude=19.0760,
            longitude=72.8777,
            city="Mumbai",
            region="West",
            area_cluster_id="CLUSTER_WEST",
            synthetic_location_group="test_group",
        )
    )
    db_session.add(
        Account(
            account_id=acc_id,
            account_type="savings",
            account_opened_at=now - timedelta(days=100),
            account_age_days=100,
            synthetic_profile_type="cashout_isolation_tester",
        )
    )
    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_id,
            fraud_type="upi_fraud",
            fraud_channel="UPI",
            fraud_amount=Decimal("30000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Cashout isolation test complaint",
        )
    )

    t_tx = now + timedelta(minutes=10)
    t_cashout = now + timedelta(hours=5)

    # Inflow transfer at t_tx
    tx = Transaction(
        transaction_id=f"TX_CSH_ISO_{uid}",
        case_id=case_id,
        from_account_id=f"ACC_OTHER_{uid}",
        to_account_id=acc_id,
        amount=Decimal("30000.00"),
        channel="UPI",
        transaction_type="transfer",
        initiated_at=t_tx,
        completed_at=t_tx + timedelta(minutes=1),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add(
        Account(
            account_id=f"ACC_OTHER_{uid}",
            account_type="savings",
            account_opened_at=now - timedelta(days=100),
            account_age_days=100,
            synthetic_profile_type="other_tester",
        )
    )
    db_session.add(tx)

    # Cashout event at t_cashout (later point in time)
    cashout = CashoutEvent(
        cashout_event_id=f"CSH_ISO_{uid}",
        case_id=case_id,
        account_id=acc_id,
        location_id=loc_id,
        transaction_id=f"TX_CSH_ISO_{uid}",
        withdrawal_amount=Decimal("20000.00"),
        cashout_occurred_at=t_cashout,
        is_future_ground_truth=False,
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add(cashout)
    db_session.commit()

    # Query before cashout occurred: as_of = t_tx + 30 min
    cutoff_before = (t_tx + timedelta(minutes=30)).isoformat()
    res_before = client.get(f"{settings.API_V1_PREFIX}/accounts/{acc_id}/network?as_of={cutoff_before}")
    assert res_before.status_code == 200
    data_before = res_before.json()
    assert "cashout_node" not in data_before["observed_roles"]

    # Query after cashout occurred: as_of = t_cashout + 10 min
    cutoff_after = (t_cashout + timedelta(minutes=10)).isoformat()
    res_after = client.get(f"{settings.API_V1_PREFIX}/accounts/{acc_id}/network?as_of={cutoff_after}")
    assert res_after.status_code == 200
    data_after = res_after.json()
    assert "cashout_node" in data_after["observed_roles"]


def test_multi_valued_account_roles(db_session):
    """Verify account roles are multi-valued (e.g., victim in one case, intermediary in another)."""
    now = datetime(2026, 1, 23, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    acc_target = f"ACC_MVR_TARGET_{uid}"
    acc_src2 = f"ACC_MVR_SRC2_{uid}"
    acc_dst2 = f"ACC_MVR_DST2_{uid}"

    case_1 = f"CASE_MVR_1_{uid}"
    case_2 = f"CASE_MVR_2_{uid}"

    for acc_id in (acc_target, acc_src2, acc_dst2):
        db_session.add(
            Account(
                account_id=acc_id,
                account_type="savings",
                account_opened_at=now - timedelta(days=150),
                account_age_days=150,
                synthetic_profile_type="mvr_tester",
            )
        )

    # Case 1: Target account is victim
    db_session.add(
        Complaint(
            case_id=case_1,
            victim_account_id=acc_target,
            fraud_type="phishing",
            fraud_channel="UPI",
            fraud_amount=Decimal("50000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Target account as victim in case 1",
        )
    )

    # Case 2: Target account acts as intermediary (receives and forwards)
    db_session.add(
        Complaint(
            case_id=case_2,
            victim_account_id=acc_src2,
            fraud_type="investment_scam",
            fraud_channel="IMPS",
            fraud_amount=Decimal("100000.00"),
            fraud_occurred_at=now + timedelta(days=1),
            complaint_registered_at=now + timedelta(days=1, hours=1),
            complaint_delay_minutes=60,
            synthetic_description="Target account as intermediary in case 2",
        )
    )

    # Case 2 Transactions: src2 -> target -> dst2
    db_session.add(
        Transaction(
            transaction_id=f"TX_MVR_1_{uid}",
            case_id=case_2,
            from_account_id=acc_src2,
            to_account_id=acc_target,
            amount=Decimal("100000.00"),
            channel="IMPS",
            transaction_type="transfer",
            initiated_at=now + timedelta(days=1, minutes=5),
            completed_at=now + timedelta(days=1, minutes=6),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.add(
        Transaction(
            transaction_id=f"TX_MVR_2_{uid}",
            case_id=case_2,
            from_account_id=acc_target,
            to_account_id=acc_dst2,
            amount=Decimal("95000.00"),
            channel="IMPS",
            transaction_type="transfer",
            initiated_at=now + timedelta(days=1, minutes=15),
            completed_at=now + timedelta(days=1, minutes=16),
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/accounts/{acc_target}/network")
    assert res.status_code == 200
    data = res.json()

    assert data["account_id"] == acc_target
    assert "victim" in data["observed_roles"]
    assert "intermediary_mule" in data["observed_roles"]
    assert len(data["participating_cases"]) == 2
    assert case_1 in data["participating_cases"]
    assert case_2 in data["participating_cases"]


def test_no_ground_truth_in_network_intelligence(db_session):
    """Verify that future ground-truth cashout records never influence network intelligence."""
    now = datetime(2026, 1, 24, 10, 0, 0)
    uid = uuid.uuid4().hex[:8].upper()

    acc_id = f"ACC_NO_GT_{uid}"
    case_id = f"CASE_NO_GT_{uid}"
    loc_id = f"LOC_NO_GT_{uid}"

    from src.backend.db.models import Location
    db_session.add(
        Location(
            location_id=loc_id,
            location_name=f"ATM Safe {uid}",
            location_type="atm",
            latitude=28.6139,
            longitude=77.2090,
            city="Delhi",
            region="North",
            area_cluster_id="CLUSTER_NORTH",
            synthetic_location_group="test_group",
        )
    )
    db_session.add(
        Account(
            account_id=acc_id,
            account_type="savings",
            account_opened_at=now - timedelta(days=100),
            account_age_days=100,
            synthetic_profile_type="no_gt_tester",
        )
    )
    db_session.add(
        Complaint(
            case_id=case_id,
            victim_account_id=acc_id,
            fraud_type="upi_fraud",
            fraud_channel="UPI",
            fraud_amount=Decimal("25000.00"),
            fraud_occurred_at=now,
            complaint_registered_at=now + timedelta(hours=1),
            complaint_delay_minutes=60,
            synthetic_description="No GT complaint",
        )
    )

    # Transaction for case
    tx_gt = Transaction(
        transaction_id=f"TX_GT_ONLY_{uid}",
        case_id=case_id,
        from_account_id=acc_id,
        to_account_id="ACC_ATM_TERMINAL",
        amount=Decimal("25000.00"),
        channel="UPI",
        transaction_type="withdrawal",
        initiated_at=now + timedelta(hours=3),
        completed_at=now + timedelta(hours=3, minutes=1),
        synthetic_event_group_id=f"GRP_{uid}",
    )
    db_session.add(tx_gt)

    # Future ground truth cashout event ONLY (no visible operational cashout)
    db_session.add(
        CashoutEvent(
            cashout_event_id=f"CSH_GT_ONLY_{uid}",
            case_id=case_id,
            account_id=acc_id,
            location_id=loc_id,
            transaction_id=f"TX_GT_ONLY_{uid}",
            withdrawal_amount=Decimal("25000.00"),
            cashout_occurred_at=now + timedelta(hours=4),
            is_future_ground_truth=True,  # STRICTLY FUTURE GROUND TRUTH
            synthetic_event_group_id=f"GRP_{uid}",
        )
    )
    db_session.commit()

    res = client.get(f"{settings.API_V1_PREFIX}/accounts/{acc_id}/network")
    assert res.status_code == 200
    data = res.json()

    # Invariant: Future GT cashout must NOT mark account as cashout_node
    assert "cashout_node" not in data["observed_roles"]
    assert "victim" in data["observed_roles"]

