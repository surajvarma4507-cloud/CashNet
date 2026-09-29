"""Cross-Case Network Intelligence and Account Syndication Service."""

import math
from collections import defaultdict
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from src.backend.db.models import (
    Account,
    CaseRelationship,
    CashoutEvent,
    Complaint,
    Transaction,
)
from src.backend.schemas import (
    AccountActivityWindow,
    AccountBase,
    AccountMoneyTrailItem,
    AccountMoneyTrailsResponse,
    AccountNetworkResponse,
    CaseNetworkMetrics,
    CaseNetworkResponse,
    CoOccurringAccountInfo,
    PaginationMeta,
    RelatedCaseEvidence,
    RelatedCaseListResponse,
)
from src.backend.services.case_service import CaseService


class NetworkService:
    """Business logic for evaluating cross-case financial syndicates and multi-case accounts."""

    @classmethod
    def get_case_network(
        cls,
        db: Session,
        case_id: str,
        max_depth: int = 2,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[CaseNetworkResponse]:
        """Discovers cross-case financial networks, shared mule accounts, and syndicate clusters."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            return None

        # 1. Identify all accounts in target case
        tx_query = db.query(Transaction).filter(Transaction.case_id == case_id)
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        current_case_txs = tx_query.all()
        current_case_accounts: Set[str] = {complaint.victim_account_id}
        for tx in current_case_txs:
            if tx.from_account_id != "ACC_ATM_TERMINAL":
                current_case_accounts.add(tx.from_account_id)
            if tx.to_account_id != "ACC_ATM_TERMINAL":
                current_case_accounts.add(tx.to_account_id)

        # 2. Query transactions involving these accounts in other cases
        other_tx_query = (
            db.query(Transaction)
            .filter(
                Transaction.case_id != case_id,
                Transaction.case_id.isnot(None),
                or_(
                    Transaction.from_account_id.in_(current_case_accounts),
                    Transaction.to_account_id.in_(current_case_accounts),
                ),
            )
        )
        if effective_as_of is not None:
            other_tx_query = other_tx_query.filter(Transaction.initiated_at <= effective_as_of)

        other_case_txs = other_tx_query.all()

        # 3. Query explicit CaseRelationship records
        rel_query = (
            db.query(CaseRelationship)
            .filter(
                or_(
                    CaseRelationship.case_id == case_id,
                    CaseRelationship.related_case_id == case_id,
                )
            )
        )
        if effective_as_of is not None:
            rel_query = rel_query.filter(CaseRelationship.relationship_created_at <= effective_as_of)

        case_relationships_db = rel_query.all()

        # 4. Compile relationship evidence
        # Aggregate transactions by (related_case_id, shared_account_id)
        link_aggregates: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(
            lambda: {
                "tx_count": 0,
                "volume": Decimal("0.00"),
                "first_seen": None,
                "last_seen": None,
                "source": "observed_transaction_graph",
                "rel_type": "shared_mule_account",
            }
        )

        for tx in other_case_txs:
            related_cid = tx.case_id
            shared_acc = tx.from_account_id if tx.from_account_id in current_case_accounts else tx.to_account_id
            if shared_acc == "ACC_ATM_TERMINAL":
                continue

            entry = link_aggregates[(related_cid, shared_acc)]
            entry["tx_count"] += 1
            entry["volume"] += tx.amount
            if entry["first_seen"] is None or tx.initiated_at < entry["first_seen"]:
                entry["first_seen"] = tx.initiated_at
            if entry["last_seen"] is None or tx.completed_at > entry["last_seen"]:
                entry["last_seen"] = tx.completed_at

        # Incorporate explicit CaseRelationship records if not already present
        for cr in case_relationships_db:
            other_cid = cr.related_case_id if cr.case_id == case_id else cr.case_id
            shared_acc = cr.account_id
            key = (other_cid, shared_acc)
            if key not in link_aggregates:
                link_aggregates[key] = {
                    "tx_count": cr.shared_transaction_count,
                    "volume": Decimal("0.00"),
                    "first_seen": cr.relationship_created_at,
                    "last_seen": cr.relationship_created_at,
                    "source": "case_relationships_record",
                    "rel_type": cr.relationship_type or "shared_mule_account",
                }

        # Build list of RelatedCaseEvidence
        relationships: List[RelatedCaseEvidence] = []
        for (rel_cid, shared_acc), data in link_aggregates.items():
            curr_role = "victim" if shared_acc == complaint.victim_account_id else "intermediary_mule"
            rel_role = "intermediary_mule"  # Neutral descriptor

            relationships.append(
                RelatedCaseEvidence(
                    related_case_id=rel_cid,
                    relationship_type=data["rel_type"],
                    shared_account_id=shared_acc,
                    shared_account_role_in_current_case=curr_role,
                    shared_account_role_in_related_case=rel_role,
                    shared_transaction_count=data["tx_count"],
                    shared_amount_volume=data["volume"],
                    first_interaction_at=data["first_seen"],
                    last_interaction_at=data["last_seen"],
                    evidence_source=data["source"],
                )
            )

        # Sort relationships by volume descending, then tx count descending
        relationships.sort(key=lambda r: (-r.shared_amount_volume, -r.shared_transaction_count))

        # Metrics calculation
        direct_shared_accounts = sorted(list({r.shared_account_id for r in relationships}))
        connected_case_ids = sorted(list({r.related_case_id for r in relationships}))
        connected_cases_count = len(connected_case_ids)
        total_syndicate_vol = sum((r.shared_amount_volume for r in relationships), Decimal("0.00"))

        # Find hub accounts (accounts connecting >= 2 distinct cases)
        acc_to_case_count: Dict[str, Set[str]] = defaultdict(set)
        for r in relationships:
            acc_to_case_count[r.shared_account_id].add(r.related_case_id)
            acc_to_case_count[r.shared_account_id].add(case_id)

        shared_hubs = sorted([
            acc for acc, c_set in acc_to_case_count.items()
            if len(c_set) >= 2
        ])

        cluster_id = f"SYNDICATE_{shared_hubs[0]}" if shared_hubs else (
            f"CLUSTER_{case_id}" if connected_cases_count > 0 else None
        )

        network_metrics = CaseNetworkMetrics(
            total_syndicate_volume=total_syndicate_vol,
            shared_hub_accounts=shared_hubs,
            cluster_id=cluster_id,
            connected_component_size=1 + connected_cases_count,
        )

        return CaseNetworkResponse(
            case_id=case_id,
            as_of=effective_as_of,
            direct_shared_accounts=direct_shared_accounts,
            connected_cases_count=connected_cases_count,
            connected_case_ids=connected_case_ids,
            relationships=relationships,
            network_metrics=network_metrics,
        )

    @classmethod
    def get_related_cases(
        cls,
        db: Session,
        case_id: str,
        page: int = 1,
        page_size: int = 20,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[RelatedCaseListResponse]:
        """Paginated list of related cases linked by shared financial infrastructure."""
        net_response = cls.get_case_network(
            db,
            case_id=case_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
        if not net_response:
            return None

        all_items = net_response.relationships
        total = len(all_items)
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        offset = (page - 1) * page_size
        paginated_items = all_items[offset : offset + page_size]

        return RelatedCaseListResponse(
            case_id=case_id,
            total_related_cases=total,
            items=paginated_items,
            pagination=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )

    @classmethod
    def get_account_network(
        cls,
        db: Session,
        account_id: str,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[AccountNetworkResponse]:
        """Provides multi-case intelligence and co-occurring accounts for an individual account."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return None

        # 1. Fetch all transactions involving this account
        tx_query = (
            db.query(Transaction)
            .filter(
                or_(
                    Transaction.from_account_id == account_id,
                    Transaction.to_account_id == account_id,
                )
            )
        )
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        transactions = tx_query.order_by(Transaction.initiated_at.asc()).all()

        # 2. Fetch complaints where account is victim
        complaint_query = db.query(Complaint).filter(Complaint.victim_account_id == account_id)
        if effective_as_of is not None:
            complaint_query = complaint_query.filter(Complaint.complaint_registered_at <= effective_as_of)
        victim_complaints = complaint_query.all()

        # 3. Aggregate activity statistics
        participating_cases: Set[str] = set()
        for c in victim_complaints:
            participating_cases.add(c.case_id)

        total_inflow = Decimal("0.00")
        total_outflow = Decimal("0.00")
        first_seen = None
        last_seen = None

        co_occurring_agg: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                "sent_count": 0,
                "received_count": 0,
                "volume": Decimal("0.00"),
                "first_seen": None,
                "last_seen": None,
            }
        )

        for tx in transactions:
            if tx.case_id:
                participating_cases.add(tx.case_id)

            if first_seen is None or tx.initiated_at < first_seen:
                first_seen = tx.initiated_at
            if last_seen is None or tx.completed_at > last_seen:
                last_seen = tx.completed_at

            if tx.from_account_id == account_id:
                total_outflow += tx.amount
                counterpart = tx.to_account_id
                if counterpart != "ACC_ATM_TERMINAL":
                    entry = co_occurring_agg[counterpart]
                    entry["sent_count"] += 1
                    entry["volume"] += tx.amount
                    if entry["first_seen"] is None or tx.initiated_at < entry["first_seen"]:
                        entry["first_seen"] = tx.initiated_at
                    if entry["last_seen"] is None or tx.completed_at > entry["last_seen"]:
                        entry["last_seen"] = tx.completed_at

            if tx.to_account_id == account_id:
                total_inflow += tx.amount
                counterpart = tx.from_account_id
                if counterpart != "ACC_ATM_TERMINAL":
                    entry = co_occurring_agg[counterpart]
                    entry["received_count"] += 1
                    entry["volume"] += tx.amount
                    if entry["first_seen"] is None or tx.initiated_at < entry["first_seen"]:
                        entry["first_seen"] = tx.initiated_at
                    if entry["last_seen"] is None or tx.completed_at > entry["last_seen"]:
                        entry["last_seen"] = tx.completed_at

        # 4. Build co-occurring accounts
        co_occurring: List[CoOccurringAccountInfo] = []
        for other_acc, data in co_occurring_agg.items():
            sent = data["sent_count"]
            recv = data["received_count"]
            if sent > 0 and recv > 0:
                rel_type = "bidirectional_transfer"
            elif sent > 0:
                rel_type = "sent_funds_to"
            else:
                rel_type = "received_funds_from"

            co_occurring.append(
                CoOccurringAccountInfo(
                    account_id=other_acc,
                    relationship_type=rel_type,
                    shared_transaction_count=sent + recv,
                    shared_volume=data["volume"],
                    first_seen_at=data["first_seen"],
                    last_seen_at=data["last_seen"],
                )
            )

        co_occurring.sort(key=lambda c: (-c.shared_volume, -c.shared_transaction_count))

        # 5. Observed roles
        observed_roles = []
        if len(victim_complaints) > 0:
            observed_roles.append("victim")
        if total_inflow > Decimal("0.00") and total_outflow > Decimal("0.00"):
            observed_roles.append("intermediary_mule")
        elif total_inflow > Decimal("0.00"):
            observed_roles.append("recipient_node")
        elif total_outflow > Decimal("0.00"):
            observed_roles.append("source_node")

        # Check for cashouts (respecting point-in-time and excluding ground truth)
        cashout_query = (
            db.query(CashoutEvent)
            .filter(
                CashoutEvent.account_id == account_id,
                CashoutEvent.is_future_ground_truth.is_(False),
            )
        )
        if effective_as_of is not None:
            cashout_query = cashout_query.filter(CashoutEvent.cashout_occurred_at <= effective_as_of)
        cashout_count = cashout_query.count()
        if cashout_count > 0:
            observed_roles.append("cashout_node")

        return AccountNetworkResponse(
            account_id=account_id,
            as_of=effective_as_of,
            account_profile=AccountBase.model_validate(account),
            observed_roles=observed_roles or ["active_account"],
            participating_cases=sorted(list(participating_cases)),
            participating_cases_count=len(participating_cases),
            total_inflow_observed=total_inflow,
            total_outflow_observed=total_outflow,
            total_transactions_count=len(transactions),
            co_occurring_accounts=co_occurring,
            activity_window=AccountActivityWindow(
                first_seen_at=first_seen,
                last_seen_at=last_seen,
            ),
        )

    @classmethod
    def get_account_money_trails(
        cls,
        db: Session,
        account_id: str,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[AccountMoneyTrailsResponse]:
        """Retrieves all case money trails that an account has participated in."""
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        account = db.query(Account).filter(Account.account_id == account_id).first()
        if not account:
            return None

        # Query all distinct cases involving this account
        tx_query = (
            db.query(Transaction.case_id)
            .filter(
                or_(
                    Transaction.from_account_id == account_id,
                    Transaction.to_account_id == account_id,
                ),
                Transaction.case_id.isnot(None),
            )
            .distinct()
        )
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        case_ids = {row[0] for row in tx_query.all()}

        # Check victim complaints
        complaint_query = db.query(Complaint.case_id).filter(Complaint.victim_account_id == account_id)
        if effective_as_of is not None:
            complaint_query = complaint_query.filter(Complaint.complaint_registered_at <= effective_as_of)
        for row in complaint_query.all():
            case_ids.add(row[0])

        money_trail_items: List[AccountMoneyTrailItem] = []
        from src.backend.services.money_trail_service import MoneyTrailService

        for cid in sorted(list(case_ids)):
            trail = MoneyTrailService.reconstruct_money_trail(
                db,
                case_id=cid,
                as_of=effective_as_of,
            )
            if not trail:
                continue

            node_match = next((n for n in trail.nodes if n.account_id == account_id), None)
            if node_match:
                money_trail_items.append(
                    AccountMoneyTrailItem(
                        case_id=cid,
                        role_in_case=node_match.role,
                        hop_level=node_match.hop_level,
                        total_received_in_case=node_match.total_received,
                        total_sent_in_case=node_match.total_sent,
                        transaction_count_in_case=node_match.in_degree + node_match.out_degree,
                    )
                )

        return AccountMoneyTrailsResponse(
            account_id=account_id,
            as_of=effective_as_of,
            total_cases=len(money_trail_items),
            money_trails=money_trail_items,
        )
