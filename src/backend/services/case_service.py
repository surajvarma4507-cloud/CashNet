"""Service layer for Case and Money Trail management."""

import math
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from src.backend.db.models import (
    Account,
    AccountLabel,
    CaseFeature,
    CaseRelationship,
    CashoutEvent,
    Complaint,
    InvestigatorAction,
    Location,
    PredictionSnapshot,
    Transaction,
)
from src.backend.schemas import (
    CaseAccountListResponse,
    CaseDetailResponse,
    CaseListResponse,
    CaseSummary,
    InvestigatorActionCreate,
    InvestigatorActionDetail,
    LinkedAccountInfo,
    PaginationMeta,
    TransactionDetail,
    TransactionListResponse,
)


class CaseService:
    """Business operations on cybercrime cases and money trail transactions."""

    @staticmethod
    def resolve_as_of_timestamp(
        db: Session,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[datetime]:
        """Resolves effective point-in-time timestamp from explicit as_of or prediction snapshot."""
        if snapshot_id is not None:
            snapshot = (
                db.query(PredictionSnapshot)
                .filter(PredictionSnapshot.snapshot_id == snapshot_id)
                .first()
            )
            if not snapshot:
                raise ValueError(f"PredictionSnapshot with ID '{snapshot_id}' not found.")
            return snapshot.prediction_timestamp
        return as_of

    @staticmethod
    def list_cases(
        db: Session,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        status: Optional[str] = None,
        fraud_type: Optional[str] = None,
        fraud_channel: Optional[str] = None,
        min_amount: Optional[float] = None,
        max_amount: Optional[float] = None,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
        as_of: Optional[datetime] = None,
        order_by: str = "complaint_registered_at",
        order_desc: bool = True,
    ) -> CaseListResponse:
        """Paginated, filtered list of cybercrime complaints with optional point-in-time filtering."""
        query = db.query(Complaint)

        # Filters
        if status:
            query = query.filter(Complaint.complaint_status == status)
        if fraud_type:
            query = query.filter(Complaint.fraud_type == fraud_type)
        if fraud_channel:
            query = query.filter(Complaint.fraud_channel == fraud_channel)
        if min_amount is not None:
            query = query.filter(Complaint.fraud_amount >= Decimal(str(min_amount)))
        if max_amount is not None:
            query = query.filter(Complaint.fraud_amount <= Decimal(str(max_amount)))
        if from_date is not None:
            query = query.filter(Complaint.complaint_registered_at >= from_date)
        if to_date is not None:
            query = query.filter(Complaint.complaint_registered_at <= to_date)
        if as_of is not None:
            query = query.filter(Complaint.complaint_registered_at <= as_of)

        # Free-text search
        if search:
            search_pattern = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    Complaint.case_id.ilike(search_pattern),
                    Complaint.victim_account_id.ilike(search_pattern),
                    Complaint.synthetic_description.ilike(search_pattern),
                )
            )

        # Total matching records
        total = query.count()
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # Sorting
        sort_column = getattr(Complaint, order_by, Complaint.complaint_registered_at)
        if order_desc:
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(sort_column)

        # Pagination offset & limit
        offset = (page - 1) * page_size
        complaints = query.offset(offset).limit(page_size).all()

        # Build summaries
        items = []
        for c in complaints:
            # Summary stats respecting point-in-time and anti-leakage invariants
            tx_q = db.query(func.count(Transaction.transaction_id)).filter(Transaction.case_id == c.case_id)
            if as_of is not None:
                tx_q = tx_q.filter(Transaction.initiated_at <= as_of)
            tx_count = tx_q.scalar() or 0

            # Exclude future ground truth cashouts
            cashout_q = (
                db.query(func.count(CashoutEvent.cashout_event_id))
                .filter(
                    CashoutEvent.case_id == c.case_id,
                    CashoutEvent.is_future_ground_truth.is_(False),
                )
            )
            if as_of is not None:
                cashout_q = cashout_q.filter(CashoutEvent.cashout_occurred_at <= as_of)
            cashout_cnt = cashout_q.scalar() or 0

            victim_loc_city = None
            if c.victim_location_id:
                loc = db.query(Location.city).filter(Location.location_id == c.victim_location_id).first()
                if loc:
                    victim_loc_city = loc[0]

            item = CaseSummary(
                case_id=c.case_id,
                victim_account_id=c.victim_account_id,
                fraud_type=c.fraud_type,
                fraud_channel=c.fraud_channel,
                fraud_amount=c.fraud_amount,
                fraud_currency=c.fraud_currency,
                fraud_occurred_at=c.fraud_occurred_at,
                complaint_registered_at=c.complaint_registered_at,
                complaint_delay_minutes=c.complaint_delay_minutes,
                victim_location_id=c.victim_location_id,
                initial_transaction_id=c.initial_transaction_id,
                complaint_status=c.complaint_status,
                synthetic_description=c.synthetic_description,
                created_at=c.created_at,
                transaction_count=tx_count,
                cashout_count=cashout_cnt,
                victim_city=victim_loc_city,
            )
            items.append(item)

        return CaseListResponse(
            items=items,
            pagination=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )

    @staticmethod
    def get_case(
        db: Session,
        case_id: str,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[CaseDetailResponse]:
        """Detailed case view with victim profile, features, cashouts, and audit actions."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        complaint = (
            db.query(Complaint)
            .options(
                joinedload(Complaint.victim_account).joinedload(Account.home_location),
                joinedload(Complaint.victim_account).joinedload(Account.label),
                joinedload(Complaint.victim_location),
                joinedload(Complaint.features),
                selectinload(Complaint.actions),
            )
            .filter(Complaint.case_id == case_id)
            .first()
        )

        if not complaint:
            return None

        # Point-in-time transactions and account involvement
        tx_query = db.query(Transaction).filter(Transaction.case_id == case_id)
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        transactions = tx_query.all()
        tx_count = len(transactions)

        accounts_involved = set()
        for t in transactions:
            accounts_involved.add(t.from_account_id)
            accounts_involved.add(t.to_account_id)
        accounts_involved.add(complaint.victim_account_id)

        # Operational cashouts: strictly exclude future ground truth cashout events and filter by effective_as_of
        cashouts_query = (
            db.query(CashoutEvent)
            .options(joinedload(CashoutEvent.location))
            .filter(
                CashoutEvent.case_id == case_id,
                CashoutEvent.is_future_ground_truth.is_(False),
            )
        )
        if effective_as_of is not None:
            cashouts_query = cashouts_query.filter(CashoutEvent.cashout_occurred_at <= effective_as_of)

        visible_cashouts = cashouts_query.order_by(CashoutEvent.cashout_occurred_at.asc()).all()
        total_cashout_amt = sum((c.withdrawal_amount for c in visible_cashouts), Decimal("0.00"))

        # Actions filtered by point-in-time if applicable
        actions = complaint.actions
        if effective_as_of is not None:
            actions = [act for act in actions if act.created_at <= effective_as_of]

        return CaseDetailResponse(
            case_id=complaint.case_id,
            victim_account_id=complaint.victim_account_id,
            fraud_type=complaint.fraud_type,
            fraud_channel=complaint.fraud_channel,
            fraud_amount=complaint.fraud_amount,
            fraud_currency=complaint.fraud_currency,
            fraud_occurred_at=complaint.fraud_occurred_at,
            complaint_registered_at=complaint.complaint_registered_at,
            complaint_delay_minutes=complaint.complaint_delay_minutes,
            victim_location_id=complaint.victim_location_id,
            initial_transaction_id=complaint.initial_transaction_id,
            complaint_status=complaint.complaint_status,
            synthetic_description=complaint.synthetic_description,
            created_at=complaint.created_at,
            victim_account=complaint.victim_account,
            victim_location=complaint.victim_location,
            features=complaint.features,
            actions=actions,
            cashouts=visible_cashouts,
            total_transactions_count=tx_count,
            total_accounts_involved=len(accounts_involved),
            total_cashout_amount=total_cashout_amt,
            is_cashout_completed=len(visible_cashouts) > 0,
        )

    @staticmethod
    def get_case_transactions(
        db: Session,
        case_id: str,
        fraud_linked_only: bool = False,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> TransactionListResponse:
        """Money trail transactions for a case ordered chronologically with optional point-in-time filtering."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        query = (
            db.query(Transaction)
            .options(joinedload(Transaction.location))
            .filter(Transaction.case_id == case_id)
        )

        if fraud_linked_only:
            query = query.filter(Transaction.is_fraud_linked.is_(True))

        if effective_as_of is not None:
            query = query.filter(Transaction.initiated_at <= effective_as_of)

        transactions = query.order_by(Transaction.initiated_at.asc()).all()
        total_amount = sum((t.amount for t in transactions), Decimal("0.00"))

        return TransactionListResponse(
            case_id=case_id,
            total_transactions=len(transactions),
            total_amount=total_amount,
            items=transactions,
        )

    @staticmethod
    def get_case_accounts(
        db: Session,
        case_id: str,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[CaseAccountListResponse]:
        """All unique accounts involved in the case money trail with role categorization."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            return None

        # Fetch transactions for this case up to effective_as_of
        tx_query = db.query(Transaction).filter(Transaction.case_id == case_id)
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        transactions = tx_query.order_by(Transaction.initiated_at.asc()).all()

        # Collect unique account IDs and analyze money flow
        account_ids = {complaint.victim_account_id}
        received_by_account: Dict[str, Decimal] = {}
        sent_by_account: Dict[str, Decimal] = {}
        tx_count_by_account: Dict[str, int] = {}
        first_hop_recipients = set()
        second_hop_recipients = set()

        # Determine transaction hops
        for tx in transactions:
            account_ids.add(tx.from_account_id)
            account_ids.add(tx.to_account_id)

            sent_by_account[tx.from_account_id] = sent_by_account.get(tx.from_account_id, Decimal("0.00")) + tx.amount
            received_by_account[tx.to_account_id] = received_by_account.get(tx.to_account_id, Decimal("0.00")) + tx.amount

            tx_count_by_account[tx.from_account_id] = tx_count_by_account.get(tx.from_account_id, 0) + 1
            tx_count_by_account[tx.to_account_id] = tx_count_by_account.get(tx.to_account_id, 0) + 1

            if tx.from_account_id == complaint.victim_account_id:
                first_hop_recipients.add(tx.to_account_id)
            elif tx.from_account_id in first_hop_recipients:
                second_hop_recipients.add(tx.to_account_id)

        # Find historical / observed cashout accounts (excluding future ground truth)
        cashout_q = (
            db.query(CashoutEvent.account_id)
            .filter(
                CashoutEvent.case_id == case_id,
                CashoutEvent.is_future_ground_truth.is_(False),
            )
        )
        if effective_as_of is not None:
            cashout_q = cashout_q.filter(CashoutEvent.cashout_occurred_at <= effective_as_of)

        cashout_accounts = set(row[0] for row in cashout_q.all())

        # Fetch accounts with labels
        accounts = (
            db.query(Account)
            .options(joinedload(Account.label))
            .filter(Account.account_id.in_(account_ids))
            .all()
        )
        acc_dict = {a.account_id: a for a in accounts}

        linked_accounts = []
        for acc_id in account_ids:
            acc = acc_dict.get(acc_id)
            if not acc:
                continue

            # Categorize role
            if acc_id == complaint.victim_account_id:
                role = "victim"
            elif acc_id in cashout_accounts:
                role = "cashout_node"
            elif acc_id in first_hop_recipients:
                role = "mule_hop_1"
            elif acc_id in second_hop_recipients:
                role = "mule_hop_2"
            else:
                role = "intermediary_mule"

            linked_accounts.append(
                LinkedAccountInfo(
                    account=acc,
                    role_in_case=role,
                    total_received=received_by_account.get(acc_id, Decimal("0.00")),
                    total_sent=sent_by_account.get(acc_id, Decimal("0.00")),
                    transaction_count=tx_count_by_account.get(acc_id, 0),
                    is_synthetic_mule=acc.label.is_synthetic_mule if acc.label else None,
                    synthetic_behaviour_type=acc.label.synthetic_behaviour_type if acc.label else None,
                )
            )

        # Sort: victim first, then by total received descending
        linked_accounts.sort(key=lambda x: (0 if x.role_in_case == "victim" else 1, -x.total_received))

        return CaseAccountListResponse(
            case_id=case_id,
            victim_account_id=complaint.victim_account_id,
            total_accounts=len(linked_accounts),
            accounts=linked_accounts,
        )

    @staticmethod
    def add_investigator_action(
        db: Session,
        case_id: str,
        action_in: InvestigatorActionCreate,
    ) -> Optional[InvestigatorActionDetail]:
        """Records an investigator audit action or decision support event."""
        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            return None

        action = InvestigatorAction(
            action_id=f"ACT_{uuid.uuid4().hex[:12].upper()}",
            case_id=case_id,
            action_type=action_in.action_type,
            notes=action_in.notes,
            performed_by=action_in.performed_by,
            action_status=action_in.action_status,
            created_at=datetime.utcnow(),
        )
        db.add(action)
        db.commit()
        db.refresh(action)
        return action
