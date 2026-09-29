import { describe, it, expect } from 'vitest';
import {
  CaseDetailResponse,
  PredictionDetailResponse,
  MoneyTrailResponse,
} from '../types/api';

describe('Data Safety, Anti-Leakage & Ethical Decision-Support Invariants', () => {
  it('strictly validates that CaseDetailResponse has no ground-truth leakage fields', () => {
    // Mock operational case response matching CaseDetailResponse schema
    const operationalCase: CaseDetailResponse = {
      case_id: 'CASE-0001',
      victim_account_id: 'ACC-0001',
      fraud_amount: 150000,
      fraud_currency: 'INR',
      fraud_type: 'Investment Scam',
      fraud_channel: 'UPI',
      fraud_occurred_at: '2026-09-01T08:00:00Z',
      complaint_registered_at: '2026-09-01T09:00:00Z',
      complaint_status: 'registered',
      complaint_delay_minutes: 60,
      total_accounts_involved: 5,
      total_transactions_count: 8,
      cashouts: [],
      total_cashout_amount: 0,
      is_cashout_completed: false,
      synthetic_description: 'Victim lured into high-yield scheme',
      created_at: '2026-09-01T09:05:00Z',
      actions: [],
    };

    const forbiddenFields = [
      'has_future_cashout',
      'actual_next_location_id',
      'actual_next_cashout_at',
      'actual_minutes_until_cashout',
      'actual_cashout_amount',
      'evaluation_status',
      'is_future_ground_truth',
    ];

    forbiddenFields.forEach((field) => {
      expect(field in operationalCase).toBe(false);
      expect((operationalCase as unknown as Record<string, unknown>)[field]).toBeUndefined();
    });
  });

  it('ensures ML Prediction structures contain structured explanations and advisory notices', () => {
    const prediction: PredictionDetailResponse = {
      prediction_id: 'PRED-0001',
      case_id: 'CASE-0001',
      account_id: 'ACC-MULE-01',
      prediction_timestamp: '2026-09-01T09:10:00Z',
      occurrence: {
        probability_future_cashout: 0.88,
        predicted_has_future_cashout: true,
        risk_tier: 'high',
        classification_threshold: 0.5,
        model_name: 'RandomForestClassifier',
        model_version: '2.0.0',
        model_status: 'active',
      },
      location_ranking: {
        strategy_used: 'distance_fallback',
        ml_ranker_status: 'fallback_active',
        status_rationale: 'RandomForest location baseline rejected due to synthetic injection artifact. Safe distance fallback operational.',
        total_candidates: 1,
        candidates: [
          {
            rank: 1,
            location_id: 'LOC-0042',
            location_name: 'Metro ATM Central',
            distance_from_account_km: 1.2,
            historical_cashout_count: 5,
            historical_case_count: 2,
            score: 0.833,
            location_type: 'ATM',
            city: 'Mumbai',
            region: 'Maharashtra',
            latitude: 19.076,
            longitude: 72.8777,
            selection_strategy: 'distance_fallback',
            rationale: 'Closest physical ATM to terminal transfer node',
          },
        ],
      },
      timing: {
        estimated_minutes_until_cashout: 35.0,
        timing_window_low_minutes: 15.0,
        timing_window_high_minutes: 55.0,
        estimated_cashout_timestamp_earliest: '2026-09-01T09:35:00Z',
        estimated_cashout_timestamp_latest: '2026-09-01T10:35:00Z',
        model_name: 'TimingBaselineRegressor',
        variance_status: 'high_uncertainty',
        disclaimer: 'High variance baseline model due to uniform synthetic delays. Use for orientation only.',
      },
      explanation: {
        summary: 'High cash-out risk detected due to rapid multi-hop dispersion within 15 minutes.',
        risk_factors: ['Hop velocity < 5 mins', 'Unregistered mule account'],
        protective_factors: ['Nighttime extraction cooldown'],
        recommended_actions: ['Prioritize surveillance on LOC-0042.', 'Issue account freeze request.'],
        advisory_disclaimer: 'This assessment is decision support only. Human review is required before legal action.',
      },
      provenance: {
        occurrence_model: { version: '2.0.0' },
        ranking_model: { strategy: 'distance_fallback' },
        timing_model: { version: '2.0.0' },
        features_used: { count: 26 },
      },
      created_at: '2026-09-01T09:10:00Z',
    };

    expect(prediction.explanation.advisory_disclaimer).toBeDefined();
    expect(prediction.explanation.advisory_disclaimer).toContain('decision support');
    expect(prediction.timing?.variance_status).toBe('high_uncertainty');
    expect(prediction.occurrence?.risk_tier).toBe('high');
    expect(prediction.location_ranking.candidates.length).toBe(1);
  });

  it('validates money trail cycle detection and node topological stratification', () => {
    const trail: MoneyTrailResponse = {
      case_id: 'CASE-0001',
      victim_account_id: 'ACC-V1',
      fraud_amount: 100000,
      summary: {
        total_transactions: 2,
        total_amount_transferred: 100000,
        unique_accounts_count: 3,
        observed_cashout_count: 0,
        total_observed_cashout_amount: 0,
      },
      nodes: [
        {
          account_id: 'ACC-V1',
          role: 'victim',
          hop_level: 0,
          in_degree: 0,
          out_degree: 1,
          total_received: 0,
          total_sent: 100000,
          net_flow: -100000,
          is_source: true,
          is_cashout: false,
          evidence_notes: ['Victim source node'],
        },
        {
          account_id: 'ACC-M1',
          role: 'layer_1_mule',
          hop_level: 1,
          in_degree: 1,
          out_degree: 1,
          total_received: 100000,
          total_sent: 100000,
          net_flow: 0,
          is_source: false,
          is_cashout: false,
          evidence_notes: ['Intermediate layering mule'],
        },
        {
          account_id: 'ACC-M2',
          role: 'destination_mule',
          hop_level: 2,
          in_degree: 1,
          out_degree: 0,
          total_received: 100000,
          total_sent: 0,
          net_flow: 100000,
          is_source: false,
          is_cashout: true,
          evidence_notes: ['Potential cashout sink'],
        },
      ],
      ledger: [
        {
          transaction_id: 'TX-1',
          from_account_id: 'ACC-V1',
          to_account_id: 'ACC-M1',
          amount: 100000,
          currency: 'INR',
          channel: 'UPI',
          transaction_type: 'transfer',
          transaction_status: 'completed',
          initiated_at: '2026-09-01T08:05:00Z',
          completed_at: '2026-09-01T08:05:30Z',
          is_fraud_linked: true,
          hop_index: 1,
          provenance_type: 'observed',
        },
        {
          transaction_id: 'TX-2',
          from_account_id: 'ACC-M1',
          to_account_id: 'ACC-M2',
          amount: 100000,
          currency: 'INR',
          channel: 'IMPS',
          transaction_type: 'transfer',
          transaction_status: 'completed',
          initiated_at: '2026-09-01T08:15:00Z',
          completed_at: '2026-09-01T08:15:20Z',
          is_fraud_linked: true,
          hop_index: 2,
          provenance_type: 'observed',
        },
      ],
      anomalies: {
        has_cycles: false,
        cycles: [],
        has_missing_links: false,
        missing_links_count: 0,
        unconnected_accounts: [],
        has_duplicate_edges: false,
        duplicate_edge_count: 0,
        has_branching: false,
        max_branching_factor: 1,
        total_hops: 2,
        max_depth: 2,
      },
    };

    expect(trail.anomalies.has_cycles).toBe(false);
    expect(trail.nodes.find((n) => n.is_source)?.hop_level).toBe(0);
    expect(trail.nodes.length).toBe(3);
    expect(trail.ledger.length).toBe(2);
  });
});
