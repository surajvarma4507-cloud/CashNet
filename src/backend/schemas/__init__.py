"""CASHNET Pydantic Request & Response Schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# Base Schemas & Pagination
# =====================================================================

class PaginationMeta(BaseModel):
    """Metadata for paginated collection responses."""
    total: int = Field(..., description="Total number of matching records")
    page: int = Field(..., ge=1, description="Current page number (1-indexed)")
    page_size: int = Field(..., ge=1, le=500, description="Items per page")
    total_pages: int = Field(..., ge=0, description="Total number of pages")


class HealthResponse(BaseModel):
    """System health check and diagnostic status response."""
    status: str = Field(..., json_schema_extra={"example": "healthy"})
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., json_schema_extra={"example": "2.0.0"})
    database_connected: bool = Field(...)
    simulation_mode: bool = Field(True, description="Disclaimer that records are synthetic prototypes")
    models_status: Dict[str, str] = Field(...)
    table_counts: Dict[str, int] = Field(default_factory=dict)


# =====================================================================
# Location Schemas
# =====================================================================

class LocationBase(BaseModel):
    location_id: str
    location_name: str
    location_type: str
    city: str
    region: str
    latitude: float
    longitude: float
    area_cluster_id: str
    synthetic_location_group: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True)


class LocationDetail(LocationBase):
    created_at: datetime


class LocationListResponse(BaseModel):
    items: List[LocationDetail]
    pagination: PaginationMeta


class LocationClusterSummary(BaseModel):
    """Aggregate summary of a spatial location cluster."""
    area_cluster_id: str
    cluster_name: str
    city: str
    region: str
    center_latitude: float
    center_longitude: float
    total_locations: int
    atm_count: int = 0
    branch_count: int = 0
    kiosk_count: int = 0
    observed_cashout_events_count: int = 0
    total_observed_cashout_volume: Decimal = Decimal("0.00")

    model_config = ConfigDict(from_attributes=True)


class LocationClusterListResponse(BaseModel):
    """Collection of spatial location clusters."""
    total_clusters: int
    items: List[LocationClusterSummary]


class LocationHotspotDetail(BaseModel):
    """Physical terminal hotspot with historical non-ground-truth cashout frequency and volume."""
    location_id: str
    location_name: str
    location_type: str
    city: str
    region: str
    latitude: float
    longitude: float
    area_cluster_id: str
    observed_cashout_count: int = 0
    total_observed_cashout_volume: Decimal = Decimal("0.00")
    activity_risk_level: str = Field("moderate", description="Activity level: high (>=5 cashouts or >=₹500k), elevated (>=2 cashouts or >=₹100k), moderate")

    model_config = ConfigDict(from_attributes=True)


class LocationHotspotListResponse(BaseModel):
    """Collection of physical terminal cashout hotspots."""
    total_hotspots: int
    items: List[LocationHotspotDetail]


# =====================================================================
# Account Schemas
# =====================================================================

class AccountBase(BaseModel):
    account_id: str
    account_type: str
    account_opened_at: datetime
    account_age_days: int
    home_location_id: Optional[str] = None
    account_status: str = "active"
    baseline_transaction_count: int = 0
    baseline_monthly_inflow: Decimal = Decimal("0.00")
    baseline_monthly_outflow: Decimal = Decimal("0.00")
    synthetic_profile_type: str

    model_config = ConfigDict(from_attributes=True)


class AccountLabelDetail(BaseModel):
    account_id: str
    is_synthetic_mule: int
    synthetic_behaviour_type: str
    label_generation_reason: str
    label_created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AccountDetail(AccountBase):
    created_at: datetime
    label: Optional[AccountLabelDetail] = None
    home_location: Optional[LocationBase] = None


class LinkedAccountInfo(BaseModel):
    account: AccountBase
    role_in_case: str = Field(..., description="Role in money trail (e.g., victim, mule_hop_1, mule_hop_2, cashout_account)")
    total_received: Decimal = Decimal("0.00")
    total_sent: Decimal = Decimal("0.00")
    transaction_count: int = 0
    is_synthetic_mule: Optional[int] = None
    synthetic_behaviour_type: Optional[str] = None


# =====================================================================
# Transaction Schemas
# =====================================================================

class TransactionBase(BaseModel):
    transaction_id: str
    case_id: Optional[str] = None
    from_account_id: str
    to_account_id: str
    amount: Decimal
    currency: str = "INR"
    transaction_type: str
    channel: str
    transaction_status: str = "completed"
    initiated_at: datetime
    completed_at: datetime
    location_id: Optional[str] = None
    is_fraud_linked: bool = False
    synthetic_event_group_id: str

    model_config = ConfigDict(from_attributes=True)


class TransactionDetail(TransactionBase):
    created_at: datetime
    location: Optional[LocationBase] = None


class TransactionListResponse(BaseModel):
    case_id: str
    total_transactions: int
    total_amount: Decimal
    items: List[TransactionDetail]


# =====================================================================
# Cashout Event & Feature Schemas
# =====================================================================

class CashoutEventDetail(BaseModel):
    cashout_event_id: str
    case_id: str
    account_id: str
    location_id: str
    transaction_id: str
    withdrawal_amount: Decimal
    cashout_occurred_at: datetime
    minutes_since_previous_transaction: Optional[int] = None
    synthetic_event_group_id: str
    created_at: datetime
    location: Optional[LocationBase] = None

    model_config = ConfigDict(from_attributes=True)


class CaseFeatureDetail(BaseModel):
    case_id: str
    fraud_amount: Decimal
    complaint_delay_minutes: int
    transaction_count: int
    unique_account_count: int
    network_depth: int
    network_branching_factor: Decimal
    cashout_count: int
    total_cashout_amount: Decimal
    distinct_cashout_locations: int
    average_transaction_amount: Decimal
    max_transaction_amount: Decimal
    synthetic_pattern_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigatorActionDetail(BaseModel):
    action_id: str
    case_id: str
    action_type: str
    notes: Optional[str] = None
    performed_by: str
    action_status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InvestigatorActionCreate(BaseModel):
    action_type: str = Field(..., description="Action type (e.g. dispatch_alert, account_freeze, note_added, review_completed)")
    notes: Optional[str] = Field(None, description="Investigator notes or rationale")
    performed_by: str = Field("investigator_lead", description="Investigator username/identifier")
    action_status: str = Field("completed", description="Action execution status")


# =====================================================================
# Case (Complaint) Schemas
# =====================================================================

class CaseSummary(BaseModel):
    case_id: str
    victim_account_id: str
    fraud_type: str
    fraud_channel: str
    fraud_amount: Decimal
    fraud_currency: str = "INR"
    fraud_occurred_at: datetime
    complaint_registered_at: datetime
    complaint_delay_minutes: int
    victim_location_id: Optional[str] = None
    initial_transaction_id: Optional[str] = None
    complaint_status: str
    synthetic_description: str
    created_at: datetime

    # Summary enrichment
    transaction_count: Optional[int] = None
    cashout_count: Optional[int] = None
    victim_city: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CaseListResponse(BaseModel):
    items: List[CaseSummary]
    pagination: PaginationMeta


class CaseDetailResponse(BaseModel):
    case_id: str
    victim_account_id: str
    fraud_type: str
    fraud_channel: str
    fraud_amount: Decimal
    fraud_currency: str = "INR"
    fraud_occurred_at: datetime
    complaint_registered_at: datetime
    complaint_delay_minutes: int
    victim_location_id: Optional[str] = None
    initial_transaction_id: Optional[str] = None
    complaint_status: str
    synthetic_description: str
    created_at: datetime

    # Related object models
    victim_account: Optional[AccountDetail] = None
    victim_location: Optional[LocationBase] = None
    features: Optional[CaseFeatureDetail] = None
    actions: List[InvestigatorActionDetail] = Field(default_factory=list)
    cashouts: List[CashoutEventDetail] = Field(default_factory=list)

    # Derived metrics
    total_transactions_count: int = 0
    total_accounts_involved: int = 0
    total_cashout_amount: Decimal = Decimal("0.00")
    is_cashout_completed: bool = False

    model_config = ConfigDict(from_attributes=True)


class CaseAccountListResponse(BaseModel):
    case_id: str
    victim_account_id: str
    total_accounts: int
    accounts: List[LinkedAccountInfo]


# =====================================================================
# Money Trail & Graph Reconstruction Schemas (Stage 2)
# =====================================================================

class MoneyTrailNode(BaseModel):
    """Enriched account node within a reconstructed money trail graph."""
    account_id: str
    role: str = Field(..., description="Neutral role description (source_account, intermediary, recipient, observed_cashout_account, unconnected_node)")
    hop_level: int = Field(..., description="Hop distance from victim/source account (0 for source, 1 for layer 1, etc., -1 if unconnected)")
    in_degree: int = 0
    out_degree: int = 0
    total_received: Decimal = Decimal("0.00")
    total_sent: Decimal = Decimal("0.00")
    net_flow: Decimal = Decimal("0.00")
    first_activity_at: Optional[datetime] = None
    last_activity_at: Optional[datetime] = None
    account_type: Optional[str] = None
    home_location_id: Optional[str] = None
    is_source: bool = False
    is_cashout: bool = False
    evidence_notes: List[str] = Field(default_factory=list, description="Neutral factual observations justifying assigned role")

    model_config = ConfigDict(from_attributes=True)


class MoneyTrailEdge(BaseModel):
    """Directed financial transaction hop in chronological money trail ledger."""
    transaction_id: str
    from_account_id: str
    to_account_id: str
    amount: Decimal
    currency: str = "INR"
    channel: str
    transaction_type: str
    transaction_status: str = "completed"
    initiated_at: datetime
    completed_at: datetime
    location_id: Optional[str] = None
    is_fraud_linked: bool = False
    hop_index: Optional[int] = Field(None, description="Hop level of this transaction edge from source")
    provenance_type: str = Field("directly_observed", description="Data provenance: directly_observed or inferred_connection")
    synthetic_event_group_id: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MoneyTrailAnomalies(BaseModel):
    """Topological graph anomalies detected within the money trail."""
    has_cycles: bool = False
    cycles: List[List[str]] = Field(default_factory=list, description="Detected directed cycles (account ID sequences)")
    has_missing_links: bool = False
    missing_links_count: int = 0
    unconnected_accounts: List[str] = Field(default_factory=list, description="Accounts present in case transactions not reachable from source")
    has_duplicate_edges: bool = False
    duplicate_edge_count: int = 0
    has_branching: bool = False
    max_branching_factor: float = 1.0
    total_hops: int = 0
    max_depth: int = 0


class MoneyTrailSummary(BaseModel):
    """Aggregate financial summary of the reconstructed money trail."""
    total_transactions: int = 0
    total_amount_transferred: Decimal = Decimal("0.00")
    unique_accounts_count: int = 0
    observed_cashout_count: int = 0
    total_observed_cashout_amount: Decimal = Decimal("0.00")


class MoneyTrailResponse(BaseModel):
    """Complete reconstructed money trail response with chronological ledger and graph nodes."""
    case_id: str
    victim_account_id: str
    fraud_amount: Decimal
    as_of: Optional[datetime] = None
    summary: MoneyTrailSummary
    ledger: List[MoneyTrailEdge] = Field(default_factory=list, description="Strictly chronological list of transfer hops")
    nodes: List[MoneyTrailNode] = Field(default_factory=list, description="Enriched account nodes participating in the money trail")
    anomalies: MoneyTrailAnomalies


class GraphNodeItem(BaseModel):
    """Lightweight node item for visual graph rendering."""
    id: str
    label: str
    role: str
    hop_level: int
    in_degree: int
    out_degree: int
    total_received: Decimal
    total_sent: Decimal
    account_type: Optional[str] = None
    is_source: bool = False
    is_cashout: bool = False


class GraphEdgeItem(BaseModel):
    """Lightweight edge item for visual graph rendering."""
    id: str
    source: str
    target: str
    amount: Decimal
    currency: str = "INR"
    channel: str
    initiated_at: datetime
    hop_index: Optional[int] = None
    is_fraud_linked: bool = False


class GraphMetrics(BaseModel):
    """Graph structural metrics for frontend visualization and topological analysis."""
    node_count: int = Field(0, description="Total unique nodes (accounts) in the case graph")
    edge_count: int = Field(0, description="Total directed transfer edges (transactions) in the case graph")
    density: float = Field(0.0, description="Directed graph density defined as |E| / (N * (N - 1)) for N > 1, 0.0 for N <= 1")
    max_depth: int = Field(0, description="Maximum shortest-path hop depth from victim/source node")
    has_cycles: bool = Field(False, description="Whether directed feedback cycles exist in the transfer graph")
    connected_components_count: int = Field(1, description="Count of weakly connected components in the undirected projection of observed trail nodes")


class CaseGraphResponse(BaseModel):
    """Visual graph representation with nodes, directed edges, and graph metrics."""
    case_id: str
    as_of: Optional[datetime] = None
    nodes: List[GraphNodeItem] = Field(default_factory=list)
    edges: List[GraphEdgeItem] = Field(default_factory=list)
    metrics: GraphMetrics


# =====================================================================
# Cross-Case Network Intelligence Schemas (Stage 2)
# =====================================================================

class RelatedCaseEvidence(BaseModel):
    """Documented evidence linking two cybercrime cases through shared financial infrastructure."""
    related_case_id: str
    relationship_type: str = Field(..., description="Observed relationship type (e.g. shared_mule_account, shared_intermediary, direct_transfer)")
    shared_account_id: str
    shared_account_role_in_current_case: str
    shared_account_role_in_related_case: str
    shared_transaction_count: int = 1
    shared_amount_volume: Decimal = Decimal("0.00")
    first_interaction_at: Optional[datetime] = None
    last_interaction_at: Optional[datetime] = None
    evidence_source: str = Field("observed_transaction_graph", description="Source of linkage: observed_transaction_graph or case_relationships_record")


class RelatedCaseListResponse(BaseModel):
    """Paginated collection of related cases linked by shared financial infrastructure."""
    case_id: str
    total_related_cases: int
    items: List[RelatedCaseEvidence]
    pagination: PaginationMeta


class CaseNetworkMetrics(BaseModel):
    """Syndicate and cluster metrics for cross-case financial network."""
    total_syndicate_volume: Decimal = Decimal("0.00")
    shared_hub_accounts: List[str] = Field(default_factory=list)
    cluster_id: Optional[str] = None
    connected_component_size: int = 1


class CaseNetworkResponse(BaseModel):
    """Cross-case syndication intelligence response showing shared accounts and linked cases."""
    case_id: str
    as_of: Optional[datetime] = None
    direct_shared_accounts: List[str] = Field(default_factory=list)
    connected_cases_count: int = 0
    connected_case_ids: List[str] = Field(default_factory=list)
    relationships: List[RelatedCaseEvidence] = Field(default_factory=list)
    network_metrics: CaseNetworkMetrics


class CoOccurringAccountInfo(BaseModel):
    """Account observed interacting with the target account across cases."""
    account_id: str
    relationship_type: str = Field(..., description="Interaction type (e.g. sent_funds_to, received_funds_from, co_participated_in_case)")
    shared_transaction_count: int = 0
    shared_volume: Decimal = Decimal("0.00")
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class AccountActivityWindow(BaseModel):
    """Earliest and latest observed activity timestamps for an account."""
    first_seen_at: Optional[datetime] = None
    last_seen_at: Optional[datetime] = None


class AccountNetworkResponse(BaseModel):
    """Multi-case intelligence profile for a single financial account."""
    account_id: str
    as_of: Optional[datetime] = None
    account_profile: Optional[AccountBase] = None
    observed_roles: List[str] = Field(default_factory=list)
    participating_cases: List[str] = Field(default_factory=list)
    participating_cases_count: int = 0
    total_inflow_observed: Decimal = Decimal("0.00")
    total_outflow_observed: Decimal = Decimal("0.00")
    total_transactions_count: int = 0
    co_occurring_accounts: List[CoOccurringAccountInfo] = Field(default_factory=list)
    activity_window: AccountActivityWindow


class AccountMoneyTrailItem(BaseModel):
    """Summary of an account's participation within a specific case money trail."""
    case_id: str
    role_in_case: str
    hop_level: int
    total_received_in_case: Decimal = Decimal("0.00")
    total_sent_in_case: Decimal = Decimal("0.00")
    transaction_count_in_case: int = 0


class AccountMoneyTrailsResponse(BaseModel):
    """List of all case money trails that an account has participated in."""
    account_id: str
    as_of: Optional[datetime] = None
    total_cases: int = 0
    money_trails: List[AccountMoneyTrailItem] = Field(default_factory=list)


# =====================================================================
# Prediction Service & Decision Support Schemas (Stage 3)
# =====================================================================

class PredictionTriggerRequest(BaseModel):
    """Request payload for triggering an on-demand or point-in-time ML prediction run."""
    snapshot_id: Optional[str] = Field(None, description="Optional snapshot ID to evaluate strictly as of snapshot point-in-time")
    as_of: Optional[datetime] = Field(None, description="Optional point-in-time timestamp cutoff")
    candidate_count: int = Field(7, ge=1, le=50, description="Number of candidate locations to rank")
    classification_threshold: float = Field(0.5, ge=0.0, le=1.0, description="Decision threshold for binary occurrence prediction")
    disclose_provenance: bool = Field(True, description="Whether to include full feature vector provenance in response")


class OccurrencePrediction(BaseModel):
    """Model A occurrence classifier output predicting future cashout likelihood."""
    probability_future_cashout: float = Field(..., ge=0.0, le=1.0, description="Probability of future cashout event")
    predicted_has_future_cashout: bool = Field(..., description="Binary prediction given threshold")
    risk_tier: str = Field(..., description="Risk tier: low (<0.30), moderate (0.30-0.60), high (0.60-0.85), critical (>=0.85)")
    classification_threshold: float = Field(0.5, description="Operating classification threshold applied")
    model_name: str = Field("occurrence_baseline", description="Underlying model identifier")
    model_version: str = Field("1.0.0", description="Model artifact version")
    model_status: str = Field("approved_active", description="Model verification status")


class RankedLocationCandidate(BaseModel):
    """Ranked physical ATM / branch terminal location candidate."""
    candidate_id: Optional[str] = None
    location_id: str
    location_name: str
    location_type: str
    city: str
    region: str
    latitude: float
    longitude: float
    distance_from_account_km: float = Field(..., description="Distance from target account home location in kilometers")
    historical_cashout_count: int = 0
    historical_case_count: int = 0
    rank: int = Field(..., ge=1, description="1-indexed candidate ranking position")
    score: float = Field(..., description="Ranking score (higher is better / closer proximity)")
    selection_strategy: str = Field("fallback_distance_baseline", description="Strategy used for ranking")
    rationale: str = Field("Ranked by geographical proximity (distance ascending) under verified baseline policy")


class LocationRankingResult(BaseModel):
    """Model B candidate ranking output with verified fallback baseline."""
    strategy_used: str = Field("fallback_distance_baseline", description="Operational ranking strategy")
    ml_ranker_status: str = Field("REJECTED_SYNTHETIC_CANDIDATE_ARTIFACT", description="ML ranking model diagnostic status")
    status_rationale: str = Field(
        "Random Forest spatial ranker rejected due to synthetic candidate injection artifact during dataset generation. Using verified distance baseline.",
        description="Detailed justification of ranking strategy",
    )
    total_candidates: int
    candidates: List[RankedLocationCandidate] = Field(default_factory=list)


class TimingPrediction(BaseModel):
    """Model C timing baseline estimate with documented high-variance disclaimer."""
    estimated_minutes_until_cashout: Optional[float] = Field(None, description="Estimated minutes until next cashout event")
    timing_window_low_minutes: Optional[float] = Field(None, description="Lower bound of estimated timing window")
    timing_window_high_minutes: Optional[float] = Field(None, description="Upper bound of estimated timing window")
    estimated_cashout_timestamp_earliest: Optional[datetime] = Field(None, description="Estimated earliest cashout datetime")
    estimated_cashout_timestamp_latest: Optional[datetime] = Field(None, description="Estimated latest cashout datetime")
    model_name: str = Field("timing_baseline", description="Timing model artifact used")
    variance_status: str = Field("high_uncertainty_experimental", description="Confidence and variance rating")
    disclaimer: str = Field(
        "Experimental baseline timing estimate. High variance (MAE ~41.8m, R² ≈ 0.0) due to uniform synthetic delays. Use only for general tactical prioritization.",
        description="Investigator guidance regarding timing uncertainty",
    )


class InvestigatorExplanation(BaseModel):
    """Objective, evidence-backed narrative decision support explanation for law enforcement."""
    summary: str = Field(..., description="Concise case posture and risk assessment narrative")
    risk_factors: List[str] = Field(default_factory=list, description="Observed factors increasing cashout likelihood")
    protective_factors: List[str] = Field(default_factory=list, description="Observed factors decreasing cashout likelihood")
    recommended_actions: List[str] = Field(default_factory=list, description="Tactical response recommendations")
    advisory_disclaimer: str = Field(
        "AI-generated advisory assessment. Tactical decisions and freeze orders must be independently verified by authorized law enforcement personnel.",
        description="Legal and procedural advisory disclaimer",
    )


class ModelProvenance(BaseModel):
    """Full reproducibility and provenance metadata for an executed prediction."""
    occurrence_model: Dict[str, Any] = Field(default_factory=dict)
    ranking_model: Dict[str, Any] = Field(default_factory=dict)
    timing_model: Dict[str, Any] = Field(default_factory=dict)
    features_used: Dict[str, Any] = Field(default_factory=dict)


class PredictionDetailResponse(BaseModel):
    """Comprehensive prediction response payload combining all model outputs and decision support."""
    prediction_id: str
    case_id: str
    snapshot_id: Optional[str] = None
    account_id: str
    prediction_timestamp: datetime
    occurrence: OccurrencePrediction
    location_ranking: LocationRankingResult
    timing: TimingPrediction
    explanation: InvestigatorExplanation
    provenance: ModelProvenance
    created_at: datetime


class PredictionSummaryItem(BaseModel):
    """Summary item for listing historical predictions."""
    prediction_id: str
    case_id: str
    snapshot_id: Optional[str] = None
    account_id: str
    prediction_timestamp: datetime
    occurrence_probability: float
    predicted_occurrence: bool
    risk_tier: str
    top_location_id: Optional[str] = None
    top_location_name: Optional[str] = None
    top_location_distance_km: Optional[float] = None
    estimated_minutes_until_cashout: Optional[float] = None
    created_at: datetime


class CasePredictionHistoryResponse(BaseModel):
    """Historical collection of prediction runs executed for a given case."""
    case_id: str
    total_predictions: int
    items: List[PredictionSummaryItem] = Field(default_factory=list)
    pagination: Optional[PaginationMeta] = None


