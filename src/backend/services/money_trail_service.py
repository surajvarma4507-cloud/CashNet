"""Money-Trail Reconstruction and Graph Topology Service."""

from collections import defaultdict, deque
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy.orm import Session, joinedload

from src.backend.db.models import (
    Account,
    CashoutEvent,
    Complaint,
    Transaction,
)
from src.backend.schemas import (
    CaseGraphResponse,
    GraphEdgeItem,
    GraphMetrics,
    GraphNodeItem,
    MoneyTrailAnomalies,
    MoneyTrailEdge,
    MoneyTrailNode,
    MoneyTrailResponse,
    MoneyTrailSummary,
)
from src.backend.services.case_service import CaseService


class MoneyTrailService:
    """Business operations for reconstructing multi-hop money trails and graph analysis."""

    @staticmethod
    def _detect_cycles(adjacency: Dict[str, List[str]]) -> List[List[str]]:
        """Detects directed cycles in the graph using Depth-First Search with 3-color states.

        Returns a list of cycles, each formatted as a list of account IDs forming the cycle loop.
        """
        WHITE = 0  # Unvisited
        GRAY = 1   # Visiting (current recursion stack)
        BLACK = 2  # Visited

        state: Dict[str, int] = defaultdict(lambda: WHITE)
        parent_path: List[str] = []
        cycles: List[List[str]] = []
        seen_cycle_tuples: Set[Tuple[str, ...]] = set()

        def dfs(u: str) -> None:
            state[u] = GRAY
            parent_path.append(u)

            for v in adjacency.get(u, []):
                if state[v] == GRAY:
                    # Found a back-edge indicating a cycle!
                    if v in parent_path:
                        idx = parent_path.index(v)
                        cycle_path = parent_path[idx:] + [v]
                        # Canonical tuple for deduplication
                        min_node = min(cycle_path[:-1])
                        min_idx = cycle_path.index(min_node)
                        canonical = tuple(cycle_path[min_idx:-1] + cycle_path[:min_idx] + [min_node])
                        if canonical not in seen_cycle_tuples:
                            seen_cycle_tuples.add(canonical)
                            cycles.append(cycle_path)
                elif state[v] == WHITE:
                    dfs(v)

            parent_path.pop()
            state[u] = BLACK

        for node in sorted(list(adjacency.keys())):
            if state[node] == WHITE:
                dfs(node)

        return cycles

    @staticmethod
    def _count_connected_components(nodes: Set[str], edges: List[Tuple[str, str]]) -> int:
        """Calculates the number of weakly connected components in the node/edge set."""
        if not nodes:
            return 0

        undirected_adj: Dict[str, Set[str]] = {n: set() for n in nodes}
        for u, v in edges:
            if u in undirected_adj:
                undirected_adj[u].add(v)
            if v in undirected_adj:
                undirected_adj[v].add(u)

        visited: Set[str] = set()
        components = 0

        for node in nodes:
            if node not in visited:
                components += 1
                queue = deque([node])
                visited.add(node)
                while queue:
                    curr = queue.popleft()
                    for neighbor in undirected_adj.get(curr, set()):
                        if neighbor not in visited:
                            visited.add(neighbor)
                            queue.append(neighbor)

        return components

    @classmethod
    def reconstruct_money_trail(
        cls,
        db: Session,
        case_id: str,
        fraud_linked_only: bool = False,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[MoneyTrailResponse]:
        """Reconstructs the multi-hop money trail from the victim account.

        Performs BFS hop-depth calculation, structural anomaly analysis (cycles, missing links,
        parallel duplicate edges, branching), neutral role assignment, and chronological ledger assembly.
        """
        effective_as_of = CaseService.resolve_as_of_timestamp(db, as_of=as_of, snapshot_id=snapshot_id)

        complaint = db.query(Complaint).filter(Complaint.case_id == case_id).first()
        if not complaint:
            return None

        victim_account_id = complaint.victim_account_id

        # 1. Fetch transactions up to point-in-time
        tx_query = db.query(Transaction).filter(Transaction.case_id == case_id)
        if fraud_linked_only:
            tx_query = tx_query.filter(Transaction.is_fraud_linked.is_(True))
        if effective_as_of is not None:
            tx_query = tx_query.filter(Transaction.initiated_at <= effective_as_of)

        transactions = tx_query.order_by(
            Transaction.initiated_at.asc(),
            Transaction.transaction_id.asc(),
        ).all()

        # 2. Fetch observed cashouts (strictly isolating future evaluation ground truth)
        cashout_query = (
            db.query(CashoutEvent)
            .filter(
                CashoutEvent.case_id == case_id,
                CashoutEvent.is_future_ground_truth.is_(False),
            )
        )
        if effective_as_of is not None:
            cashout_query = cashout_query.filter(CashoutEvent.cashout_occurred_at <= effective_as_of)

        visible_cashouts = cashout_query.all()
        observed_cashout_accs = {c.account_id for c in visible_cashouts}

        # 3. Collect accounts and aggregate flow statistics
        all_account_ids: Set[str] = {victim_account_id}
        in_degree: Dict[str, int] = defaultdict(int)
        out_degree: Dict[str, int] = defaultdict(int)
        total_received: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        total_sent: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        first_activity: Dict[str, datetime] = {}
        last_activity: Dict[str, datetime] = {}
        adjacency: Dict[str, List[str]] = defaultdict(list)
        pair_counts: Dict[Tuple[str, str], int] = defaultdict(int)

        for tx in transactions:
            u, v = tx.from_account_id, tx.to_account_id
            all_account_ids.add(u)
            all_account_ids.add(v)

            out_degree[u] += 1
            in_degree[v] += 1
            total_sent[u] += tx.amount
            total_received[v] += tx.amount
            adjacency[u].append(v)
            pair_counts[(u, v)] += 1

            for acc in (u, v):
                if acc not in first_activity or tx.initiated_at < first_activity[acc]:
                    first_activity[acc] = tx.initiated_at
                if acc not in last_activity or tx.completed_at > last_activity[acc]:
                    last_activity[acc] = tx.completed_at

        # 4. Breadth-First Search (BFS) for Hop-Depth Indexing starting from victim/source
        hop_distance: Dict[str, int] = {}
        if victim_account_id in all_account_ids:
            hop_distance[victim_account_id] = 0
            queue = deque([victim_account_id])
            while queue:
                curr = queue.popleft()
                curr_hop = hop_distance[curr]
                for nxt in adjacency.get(curr, []):
                    if nxt not in hop_distance:
                        hop_distance[nxt] = curr_hop + 1
                        queue.append(nxt)

        # 5. Build Chronological MoneyTrailEdge list
        ledger: List[MoneyTrailEdge] = []
        for tx in transactions:
            u = tx.from_account_id
            # If source account was reached, edge hop is (source_hop + 1)
            hop_idx = (hop_distance[u] + 1) if u in hop_distance else None
            edge = MoneyTrailEdge(
                transaction_id=tx.transaction_id,
                from_account_id=tx.from_account_id,
                to_account_id=tx.to_account_id,
                amount=tx.amount,
                currency=tx.currency,
                channel=tx.channel,
                transaction_type=tx.transaction_type,
                transaction_status=tx.transaction_status,
                initiated_at=tx.initiated_at,
                completed_at=tx.completed_at,
                location_id=tx.location_id,
                is_fraud_linked=tx.is_fraud_linked,
                hop_index=hop_idx,
                provenance_type="directly_observed",
                synthetic_event_group_id=tx.synthetic_event_group_id,
            )
            ledger.append(edge)

        # 6. Structural Anomaly Detection
        # Cycles
        cycles = cls._detect_cycles(adjacency)
        has_cycles = len(cycles) > 0

        # Missing / Unconnected Links (accounts in transactions not reachable from victim)
        unconnected_accounts = [
            acc for acc in all_account_ids
            if acc != victim_account_id and acc not in hop_distance
        ]
        has_missing_links = len(unconnected_accounts) > 0

        # Duplicate parallel edges
        duplicate_edge_count = sum(cnt - 1 for cnt in pair_counts.values() if cnt > 1)
        has_duplicate_edges = duplicate_edge_count > 0

        # Branching factor
        max_branching = max(out_degree.values()) if out_degree else 1
        has_branching = max_branching > 1

        # Max depth & total hops
        max_depth = max(hop_distance.values()) if hop_distance else 0
        total_hops = len(ledger)

        anomalies = MoneyTrailAnomalies(
            has_cycles=has_cycles,
            cycles=cycles,
            has_missing_links=has_missing_links,
            missing_links_count=len(unconnected_accounts),
            unconnected_accounts=sorted(unconnected_accounts),
            has_duplicate_edges=has_duplicate_edges,
            duplicate_edge_count=duplicate_edge_count,
            has_branching=has_branching,
            max_branching_factor=float(max_branching),
            total_hops=total_hops,
            max_depth=max_depth,
        )

        # 7. Fetch account metadata for node enrichment
        accounts_db = (
            db.query(Account)
            .filter(Account.account_id.in_(all_account_ids))
            .all()
        )
        acc_dict = {a.account_id: a for a in accounts_db}

        # 8. Build Enriched Nodes with Neutral Evidence-Based Roles
        nodes: List[MoneyTrailNode] = []
        for acc_id in all_account_ids:
            acc_obj = acc_dict.get(acc_id)
            in_deg = in_degree.get(acc_id, 0)
            out_deg = out_degree.get(acc_id, 0)
            rec_amt = total_received.get(acc_id, Decimal("0.00"))
            sent_amt = total_sent.get(acc_id, Decimal("0.00"))
            net_flow = rec_amt - sent_amt
            hop = hop_distance.get(acc_id, -1)
            is_src = (acc_id == victim_account_id)
            is_cash = (acc_id in observed_cashout_accs or acc_id == "ACC_ATM_TERMINAL")

            evidence_notes = []
            if is_src:
                role = "source_account"
                evidence_notes.append("Initial complainant / victim account originating fraud incident")
            elif is_cash:
                role = "observed_cashout_account"
                evidence_notes.append("Observed physical ATM / branch terminal cash withdrawal milestone")
            elif acc_id in unconnected_accounts:
                role = "unconnected_node"
                evidence_notes.append("Observed in case transactions but disconnected from victim source path")
            elif in_deg > 0 and out_deg > 0:
                role = "intermediary"
                evidence_notes.append(
                    f"Transit intermediary: received INR {rec_amt:,.2f} across {in_deg} transaction(s) "
                    f"and forwarded INR {sent_amt:,.2f} across {out_deg} outbound transaction(s)"
                )
            elif in_deg > 0 and out_deg == 0:
                role = "recipient"
                evidence_notes.append(
                    f"Terminal transfer recipient: received INR {rec_amt:,.2f} with unforwarded remaining balance"
                )
            else:
                role = "intermediary"
                evidence_notes.append(f"Account observed in money trail with {out_deg} outbound transfer(s)")

            nodes.append(
                MoneyTrailNode(
                    account_id=acc_id,
                    role=role,
                    hop_level=hop,
                    in_degree=in_deg,
                    out_degree=out_deg,
                    total_received=rec_amt,
                    total_sent=sent_amt,
                    net_flow=net_flow,
                    first_activity_at=first_activity.get(acc_id),
                    last_activity_at=last_activity.get(acc_id),
                    account_type=acc_obj.account_type if acc_obj else None,
                    home_location_id=acc_obj.home_location_id if acc_obj else None,
                    is_source=is_src,
                    is_cashout=is_cash,
                    evidence_notes=evidence_notes,
                )
            )

        # Sort nodes: source first, then by hop level ascending, then by total received descending
        nodes.sort(
            key=lambda n: (
                0 if n.is_source else 1,
                999 if n.hop_level < 0 else n.hop_level,
                -n.total_received,
            )
        )

        # 9. Build Summary
        total_tx_amount = sum((t.amount for t in transactions), Decimal("0.00"))
        total_cashout_amt = sum((c.withdrawal_amount for c in visible_cashouts), Decimal("0.00"))

        summary = MoneyTrailSummary(
            total_transactions=len(transactions),
            total_amount_transferred=total_tx_amount,
            unique_accounts_count=len(nodes),
            observed_cashout_count=len(visible_cashouts),
            total_observed_cashout_amount=total_cashout_amt,
        )

        return MoneyTrailResponse(
            case_id=case_id,
            victim_account_id=victim_account_id,
            fraud_amount=complaint.fraud_amount,
            as_of=effective_as_of,
            summary=summary,
            ledger=ledger,
            nodes=nodes,
            anomalies=anomalies,
        )

    @classmethod
    def get_case_graph(
        cls,
        db: Session,
        case_id: str,
        as_of: Optional[datetime] = None,
        snapshot_id: Optional[str] = None,
    ) -> Optional[CaseGraphResponse]:
        """Provides a lightweight visual graph representation with nodes, directed edges, and topology metrics."""
        trail = cls.reconstruct_money_trail(
            db,
            case_id=case_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
        if not trail:
            return None

        # Build GraphNodeItems
        graph_nodes: List[GraphNodeItem] = []
        for n in trail.nodes:
            label = f"{n.account_id} ({n.role})"
            graph_nodes.append(
                GraphNodeItem(
                    id=n.account_id,
                    label=label,
                    role=n.role,
                    hop_level=n.hop_level,
                    in_degree=n.in_degree,
                    out_degree=n.out_degree,
                    total_received=n.total_received,
                    total_sent=n.total_sent,
                    account_type=n.account_type,
                    is_source=n.is_source,
                    is_cashout=n.is_cashout,
                )
            )

        # Build GraphEdgeItems
        graph_edges: List[GraphEdgeItem] = []
        edge_pairs: List[Tuple[str, str]] = []
        for e in trail.ledger:
            graph_edges.append(
                GraphEdgeItem(
                    id=e.transaction_id,
                    source=e.from_account_id,
                    target=e.to_account_id,
                    amount=e.amount,
                    currency=e.currency,
                    channel=e.channel,
                    initiated_at=e.initiated_at,
                    hop_index=e.hop_index,
                    is_fraud_linked=e.is_fraud_linked,
                )
            )
            edge_pairs.append((e.from_account_id, e.to_account_id))

        # Graph Metrics
        node_count = len(graph_nodes)
        edge_count = len(graph_edges)
        density = (
            (edge_count / (node_count * (node_count - 1)))
            if node_count > 1
            else 0.0
        )
        all_nodes_set = {n.account_id for n in trail.nodes}
        connected_components = cls._count_connected_components(all_nodes_set, edge_pairs)

        metrics = GraphMetrics(
            node_count=node_count,
            edge_count=edge_count,
            density=round(density, 4),
            max_depth=trail.anomalies.max_depth,
            has_cycles=trail.anomalies.has_cycles,
            connected_components_count=connected_components,
        )

        return CaseGraphResponse(
            case_id=case_id,
            as_of=trail.as_of,
            nodes=graph_nodes,
            edges=graph_edges,
            metrics=metrics,
        )
