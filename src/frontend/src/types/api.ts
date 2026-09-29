/**
 * CASHNET TypeScript Type Definitions & API Contracts
 * Strictly aligned with FastAPI Backend Schemas (src/backend/schemas/__init__.py)
 */

export interface PaginationMeta {
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface HealthResponse {
  status: string;
  timestamp: string;
  version: string;
  database_connected: boolean;
  simulation_mode: boolean;
  models_status: Record<string, string>;
  table_counts: Record<string, number>;
}

export interface LocationBase {
  location_id: string;
  location_name: string;
  location_type: string;
  city: string;
  region: string;
  latitude: number;
  longitude: number;
  area_cluster_id: string;
  synthetic_location_group: string;
  is_active: boolean;
}

export interface LocationDetail extends LocationBase {
  created_at: string;
}

export interface LocationListResponse {
  items: LocationDetail[];
  pagination: PaginationMeta;
}

export interface NearbyLocationsResponse {
  query_latitude: number;
  query_longitude: number;
  radius_km: number;
  count: number;
  items: LocationDetail[];
}

export interface LocationClusterSummary {
  area_cluster_id: string;
  cluster_name: string;
  city: string;
  region: string;
  center_latitude: number;
  center_longitude: number;
  total_locations: number;
  atm_count: number;
  branch_count: number;
  kiosk_count: number;
  observed_cashout_events_count: number;
  total_observed_cashout_volume: number | string;
}

export interface LocationClusterListResponse {
  total_clusters: number;
  items: LocationClusterSummary[];
}

export interface LocationHotspotDetail {
  location_id: string;
  location_name: string;
  location_type: string;
  city: string;
  region: string;
  latitude: number;
  longitude: number;
  area_cluster_id: string;
  observed_cashout_count: number;
  total_observed_cashout_volume: number | string;
  activity_risk_level: 'high' | 'elevated' | 'moderate';
}

export interface LocationHotspotListResponse {
  total_hotspots: number;
  items: LocationHotspotDetail[];
}

export interface AccountBase {
  account_id: string;
  account_type: string;
  account_opened_at: string;
  account_age_days: number;
  home_location_id: string | null;
  account_status: string;
  baseline_transaction_count: number;
  baseline_monthly_inflow: number | string;
  baseline_monthly_outflow: number | string;
  synthetic_profile_type: string;
}

export interface AccountLabelDetail {
  account_id: string;
  is_synthetic_mule: number;
  synthetic_behaviour_type: string;
  label_generation_reason: string;
  label_created_at: string;
}

export interface AccountDetail extends AccountBase {
  created_at: string;
  label?: AccountLabelDetail | null;
  home_location?: LocationBase | null;
}

export interface LinkedAccountInfo {
  account: AccountBase;
  role_in_case: string;
  total_received: number | string;
  total_sent: number | string;
  transaction_count: number;
  is_synthetic_mule?: number | null;
  synthetic_behaviour_type?: string | null;
}

export interface TransactionBase {
  transaction_id: string;
  case_id?: string | null;
  from_account_id: string;
  to_account_id: string;
  amount: number | string;
  currency: string;
  transaction_type: string;
  channel: string;
  transaction_status: string;
  initiated_at: string;
  completed_at: string;
  location_id?: string | null;
  is_fraud_linked: boolean;
  synthetic_event_group_id: string;
}

export interface TransactionDetail extends TransactionBase {
  created_at: string;
  location?: LocationBase | null;
}

export interface TransactionListResponse {
  case_id: string;
  total_transactions: number;
  total_amount: number | string;
  items: TransactionDetail[];
}

export interface CashoutEventDetail {
  cashout_event_id: string;
  case_id: string;
  account_id: string;
  location_id: string;
  transaction_id: string;
  withdrawal_amount: number | string;
  cashout_occurred_at: string;
  minutes_since_previous_transaction?: number | null;
  synthetic_event_group_id: string;
  created_at: string;
  location?: LocationBase | null;
}

export interface CaseFeatureDetail {
  case_id: string;
  fraud_amount: number | string;
  complaint_delay_minutes: number;
  transaction_count: number;
  unique_account_count: number;
  network_depth: number;
  network_branching_factor: number | string;
  cashout_count: number;
  total_cashout_amount: number | string;
  distinct_cashout_locations: number;
  average_transaction_amount: number | string;
  max_transaction_amount: number | string;
  synthetic_pattern_type: string;
  created_at: string;
}

export type ActionType =
  | 'account_freeze'
  | 'dispatch_alert'
  | 'bank_subpoena'
  | 'surveillance_requested'
  | 'note_added'
  | 'case_reclassified';

export interface InvestigatorActionDetail {
  action_id: string;
  case_id: string;
  action_type: string;
  notes?: string | null;
  performed_by: string;
  action_status: string;
  created_at: string;
}

export interface InvestigatorActionCreate {
  action_type: string;
  notes?: string | null;
  performed_by?: string;
  action_status?: string;
}

export interface CaseSummary {
  case_id: string;
  victim_account_id: string;
  fraud_type: string;
  fraud_channel: string;
  fraud_amount: number | string;
  fraud_currency: string;
  fraud_occurred_at: string;
  complaint_registered_at: string;
  complaint_delay_minutes: number;
  victim_location_id?: string | null;
  initial_transaction_id?: string | null;
  complaint_status: string;
  synthetic_description: string;
  created_at: string;
  transaction_count?: number | null;
  cashout_count?: number | null;
  victim_city?: string | null;
}

export interface CaseListResponse {
  items: CaseSummary[];
  pagination: PaginationMeta;
}

export interface CaseDetailResponse {
  case_id: string;
  victim_account_id: string;
  fraud_type: string;
  fraud_channel: string;
  fraud_amount: number | string;
  fraud_currency: string;
  fraud_occurred_at: string;
  complaint_registered_at: string;
  complaint_delay_minutes: number;
  victim_location_id?: string | null;
  initial_transaction_id?: string | null;
  complaint_status: string;
  synthetic_description: string;
  created_at: string;
  victim_account?: AccountDetail | null;
  victim_location?: LocationBase | null;
  features?: CaseFeatureDetail | null;
  actions: InvestigatorActionDetail[];
  cashouts: CashoutEventDetail[];
  total_transactions_count: number;
  total_accounts_involved: number;
  total_cashout_amount: number | string;
  is_cashout_completed: boolean;
}

export interface CaseAccountListResponse {
  case_id: string;
  victim_account_id: string;
  total_accounts: number;
  accounts: LinkedAccountInfo[];
}

export interface MoneyTrailNode {
  account_id: string;
  role: string;
  hop_level: number;
  in_degree: number;
  out_degree: number;
  total_received: number | string;
  total_sent: number | string;
  net_flow: number | string;
  first_activity_at?: string | null;
  last_activity_at?: string | null;
  account_type?: string | null;
  home_location_id?: string | null;
  is_source: boolean;
  is_cashout: boolean;
  evidence_notes: string[];
}

export interface MoneyTrailEdge {
  transaction_id: string;
  from_account_id: string;
  to_account_id: string;
  amount: number | string;
  currency: string;
  channel: string;
  transaction_type: string;
  transaction_status: string;
  initiated_at: string;
  completed_at: string;
  location_id?: string | null;
  is_fraud_linked: boolean;
  hop_index?: number | null;
  provenance_type: string;
  synthetic_event_group_id?: string | null;
}

export interface MoneyTrailAnomalies {
  has_cycles: boolean;
  cycles: string[][];
  has_missing_links: boolean;
  missing_links_count: number;
  unconnected_accounts: string[];
  has_duplicate_edges: boolean;
  duplicate_edge_count: number;
  has_branching: boolean;
  max_branching_factor: number;
  total_hops: number;
  max_depth: number;
}

export interface MoneyTrailSummary {
  total_transactions: number;
  total_amount_transferred: number | string;
  unique_accounts_count: number;
  observed_cashout_count: number;
  total_observed_cashout_amount: number | string;
}

export interface MoneyTrailResponse {
  case_id: string;
  victim_account_id: string;
  fraud_amount: number | string;
  as_of?: string | null;
  summary: MoneyTrailSummary;
  ledger: MoneyTrailEdge[];
  nodes: MoneyTrailNode[];
  anomalies: MoneyTrailAnomalies;
}

export interface GraphNodeItem {
  id: string;
  label: string;
  role: string;
  hop_level: number;
  in_degree: number;
  out_degree: number;
  total_received: number | string;
  total_sent: number | string;
  account_type?: string | null;
  is_source: boolean;
  is_cashout: boolean;
}

export interface GraphEdgeItem {
  id: string;
  source: string;
  target: string;
  amount: number | string;
  currency: string;
  channel: string;
  initiated_at: string;
  hop_index?: number | null;
  is_fraud_linked: boolean;
}

export interface GraphMetrics {
  node_count: number;
  edge_count: number;
  density: number;
  max_depth: number;
  has_cycles: boolean;
  connected_components_count: number;
}

export interface CaseGraphResponse {
  case_id: string;
  as_of?: string | null;
  nodes: GraphNodeItem[];
  edges: GraphEdgeItem[];
  metrics: GraphMetrics;
}

export interface RelatedCaseEvidence {
  related_case_id: string;
  relationship_type: string;
  shared_account_id: string;
  shared_account_role_in_current_case: string;
  shared_account_role_in_related_case: string;
  shared_transaction_count: number;
  shared_amount_volume: number | string;
  first_interaction_at?: string | null;
  last_interaction_at?: string | null;
  evidence_source: string;
}

export interface RelatedCaseListResponse {
  case_id: string;
  total_related_cases: number;
  items: RelatedCaseEvidence[];
  pagination: PaginationMeta;
}

export interface CaseNetworkMetrics {
  total_syndicate_volume: number | string;
  shared_hub_accounts: string[];
  cluster_id?: string | null;
  connected_component_size: number;
}

export interface CaseNetworkResponse {
  case_id: string;
  as_of?: string | null;
  direct_shared_accounts: string[];
  connected_cases_count: number;
  connected_case_ids: string[];
  relationships: RelatedCaseEvidence[];
  network_metrics: CaseNetworkMetrics;
}

export interface CoOccurringAccountInfo {
  account_id: string;
  relationship_type: string;
  shared_transaction_count: number;
  shared_volume: number | string;
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface AccountActivityWindow {
  first_seen_at?: string | null;
  last_seen_at?: string | null;
}

export interface AccountNetworkResponse {
  account_id: string;
  as_of?: string | null;
  account_profile?: AccountBase | null;
  observed_roles: string[];
  participating_cases: string[];
  participating_cases_count: number;
  total_inflow_observed: number | string;
  total_outflow_observed: number | string;
  total_transactions_count: number;
  co_occurring_accounts: CoOccurringAccountInfo[];
  activity_window: AccountActivityWindow;
}

export interface AccountMoneyTrailItem {
  case_id: string;
  role_in_case: string;
  hop_level: number;
  total_received_in_case: number | string;
  total_sent_in_case: number | string;
  transaction_count_in_case: number;
}

export interface AccountMoneyTrailsResponse {
  account_id: string;
  as_of?: string | null;
  total_cases: number;
  money_trails: AccountMoneyTrailItem[];
}

export interface OccurrencePrediction {
  probability_future_cashout: number;
  predicted_has_future_cashout: boolean;
  risk_tier: string;
  classification_threshold: number;
  model_name: string;
  model_version: string;
  model_status: string;
}

export interface RankedLocationCandidate {
  candidate_id?: string | null;
  location_id: string;
  location_name: string;
  location_type: string;
  city: string;
  region: string;
  latitude: number;
  longitude: number;
  distance_from_account_km: number;
  historical_cashout_count: number;
  historical_case_count: number;
  rank: number;
  score: number;
  selection_strategy: string;
  rationale: string;
}

export interface LocationRankingResult {
  strategy_used: string;
  ml_ranker_status: string;
  status_rationale: string;
  total_candidates: number;
  candidates: RankedLocationCandidate[];
}

export interface TimingPrediction {
  estimated_minutes_until_cashout?: number | null;
  timing_window_low_minutes?: number | null;
  timing_window_high_minutes?: number | null;
  estimated_cashout_timestamp_earliest?: string | null;
  estimated_cashout_timestamp_latest?: string | null;
  model_name: string;
  variance_status: string;
  disclaimer: string;
}

export interface InvestigatorExplanation {
  summary: string;
  risk_factors: string[];
  protective_factors: string[];
  recommended_actions: string[];
  advisory_disclaimer: string;
}

export interface ModelProvenance {
  occurrence_model: Record<string, unknown>;
  ranking_model: Record<string, unknown>;
  timing_model: Record<string, unknown>;
  features_used: Record<string, unknown>;
}

export interface PredictionDetailResponse {
  prediction_id: string;
  case_id: string;
  snapshot_id?: string | null;
  account_id: string;
  prediction_timestamp: string;
  occurrence: OccurrencePrediction;
  location_ranking: LocationRankingResult;
  timing: TimingPrediction;
  explanation: InvestigatorExplanation;
  provenance: ModelProvenance;
  created_at: string;
}

export interface PredictionSummaryItem {
  prediction_id: string;
  case_id: string;
  snapshot_id?: string | null;
  account_id: string;
  prediction_timestamp: string;
  occurrence_probability: number;
  predicted_occurrence: boolean;
  risk_tier: string;
  top_location_id?: string | null;
  top_location_name?: string | null;
  top_location_distance_km?: number | null;
  estimated_minutes_until_cashout?: number | null;
  created_at: string;
}

export interface CasePredictionHistoryResponse {
  case_id: string;
  total_predictions: number;
  items: PredictionSummaryItem[];
  pagination?: PaginationMeta | null;
}
