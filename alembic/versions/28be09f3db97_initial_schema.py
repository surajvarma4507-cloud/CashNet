"""initial_schema

Revision ID: 28be09f3db97
Revises:
Create Date: 2026-09-28 18:57:16.996354

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '28be09f3db97'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all CASHNET core tables, constraints, and indexes."""
    # 1. Locations
    op.create_table(
        'locations',
        sa.Column('location_id', sa.String(length=64), primary_key=True),
        sa.Column('location_name', sa.String(length=128), nullable=False),
        sa.Column('location_type', sa.String(length=32), nullable=False),
        sa.Column('city', sa.String(length=64), nullable=False),
        sa.Column('region', sa.String(length=64), nullable=False),
        sa.Column('latitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('longitude', sa.Numeric(precision=9, scale=6), nullable=False),
        sa.Column('area_cluster_id', sa.String(length=64), nullable=False),
        sa.Column('synthetic_location_group', sa.String(length=64), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('location_id', name=op.f('pk_locations'))
    )
    with op.batch_alter_table('locations', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_locations_city'), ['city'], unique=False)
        batch_op.create_index(batch_op.f('ix_locations_region'), ['region'], unique=False)
        batch_op.create_index(batch_op.f('ix_locations_area_cluster_id'), ['area_cluster_id'], unique=False)

    # 2. Accounts
    op.create_table(
        'accounts',
        sa.Column('account_id', sa.String(length=64), primary_key=True),
        sa.Column('account_type', sa.String(length=32), nullable=False),
        sa.Column('account_opened_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('account_age_days', sa.Integer(), nullable=False),
        sa.Column('home_location_id', sa.String(length=64), nullable=True),
        sa.Column('account_status', sa.String(length=32), nullable=False, server_default='active'),
        sa.Column('baseline_transaction_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('baseline_monthly_inflow', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('baseline_monthly_outflow', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('synthetic_profile_type', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['home_location_id'], ['locations.location_id'], name=op.f('fk_accounts_home_location_id_locations')),
        sa.PrimaryKeyConstraint('account_id', name=op.f('pk_accounts'))
    )
    with op.batch_alter_table('accounts', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_accounts_account_type'), ['account_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_accounts_home_location_id'), ['home_location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_accounts_account_status'), ['account_status'], unique=False)

    # 3. Account Labels
    op.create_table(
        'account_labels',
        sa.Column('account_id', sa.String(length=64), primary_key=True),
        sa.Column('is_synthetic_mule', sa.Integer(), nullable=False),
        sa.Column('synthetic_behaviour_type', sa.String(length=64), nullable=False),
        sa.Column('label_generation_reason', sa.String(length=255), nullable=False),
        sa.Column('label_created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name=op.f('fk_account_labels_account_id_accounts')),
        sa.PrimaryKeyConstraint('account_id', name=op.f('pk_account_labels'))
    )
    with op.batch_alter_table('account_labels', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_account_labels_is_synthetic_mule'), ['is_synthetic_mule'], unique=False)

    # 4. Complaints
    op.create_table(
        'complaints',
        sa.Column('case_id', sa.String(length=64), primary_key=True),
        sa.Column('victim_account_id', sa.String(length=64), nullable=False),
        sa.Column('fraud_type', sa.String(length=64), nullable=False),
        sa.Column('fraud_channel', sa.String(length=32), nullable=False),
        sa.Column('fraud_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('fraud_currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('fraud_occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('complaint_registered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('complaint_delay_minutes', sa.Integer(), nullable=False),
        sa.Column('victim_location_id', sa.String(length=64), nullable=True),
        sa.Column('initial_transaction_id', sa.String(length=64), nullable=True),
        sa.Column('complaint_status', sa.String(length=32), nullable=False, server_default='registered'),
        sa.Column('synthetic_description', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['victim_account_id'], ['accounts.account_id'], name=op.f('fk_complaints_victim_account_id_accounts')),
        sa.ForeignKeyConstraint(['victim_location_id'], ['locations.location_id'], name=op.f('fk_complaints_victim_location_id_locations')),
        sa.PrimaryKeyConstraint('case_id', name=op.f('pk_complaints'))
    )
    with op.batch_alter_table('complaints', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_complaints_victim_account_id'), ['victim_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_fraud_type'), ['fraud_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_fraud_channel'), ['fraud_channel'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_fraud_occurred_at'), ['fraud_occurred_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_complaint_registered_at'), ['complaint_registered_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_victim_location_id'), ['victim_location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_complaints_complaint_status'), ['complaint_status'], unique=False)

    # 5. Transactions
    op.create_table(
        'transactions',
        sa.Column('transaction_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=True),
        sa.Column('from_account_id', sa.String(length=64), nullable=False),
        sa.Column('to_account_id', sa.String(length=64), nullable=False),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('currency', sa.String(length=8), nullable=False, server_default='INR'),
        sa.Column('transaction_type', sa.String(length=32), nullable=False),
        sa.Column('channel', sa.String(length=32), nullable=False),
        sa.Column('transaction_status', sa.String(length=32), nullable=False, server_default='completed'),
        sa.Column('initiated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=True),
        sa.Column('is_fraud_linked', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('synthetic_event_group_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_transactions_case_id_complaints')),
        sa.ForeignKeyConstraint(['from_account_id'], ['accounts.account_id'], name=op.f('fk_transactions_from_account_id_accounts')),
        sa.ForeignKeyConstraint(['to_account_id'], ['accounts.account_id'], name=op.f('fk_transactions_to_account_id_accounts')),
        sa.ForeignKeyConstraint(['location_id'], ['locations.location_id'], name=op.f('fk_transactions_location_id_locations')),
        sa.PrimaryKeyConstraint('transaction_id', name=op.f('pk_transactions'))
    )
    with op.batch_alter_table('transactions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_transactions_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_from_account_id'), ['from_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_to_account_id'), ['to_account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_transaction_type'), ['transaction_type'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_channel'), ['channel'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_initiated_at'), ['initiated_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_completed_at'), ['completed_at'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_location_id'), ['location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_transactions_is_fraud_linked'), ['is_fraud_linked'], unique=False)

    # 6. Cashout Events
    op.create_table(
        'cashout_events',
        sa.Column('cashout_event_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('transaction_id', sa.String(length=64), nullable=False),
        sa.Column('withdrawal_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('cashout_occurred_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('minutes_since_previous_transaction', sa.Integer(), nullable=True),
        sa.Column('is_future_ground_truth', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('synthetic_event_group_id', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_cashout_events_case_id_complaints')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name=op.f('fk_cashout_events_account_id_accounts')),
        sa.ForeignKeyConstraint(['location_id'], ['locations.location_id'], name=op.f('fk_cashout_events_location_id_locations')),
        sa.ForeignKeyConstraint(['transaction_id'], ['transactions.transaction_id'], name=op.f('fk_cashout_events_transaction_id_transactions')),
        sa.PrimaryKeyConstraint('cashout_event_id', name=op.f('pk_cashout_events'))
    )
    with op.batch_alter_table('cashout_events', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_cashout_events_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cashout_events_account_id'), ['account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cashout_events_location_id'), ['location_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cashout_events_transaction_id'), ['transaction_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_cashout_events_cashout_occurred_at'), ['cashout_occurred_at'], unique=False)

    # 7. Prediction Snapshots
    op.create_table(
        'prediction_snapshots',
        sa.Column('snapshot_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('complaint_delay_minutes', sa.Integer(), nullable=False),
        sa.Column('minutes_since_last_transaction', sa.Integer(), nullable=True),
        sa.Column('incoming_transaction_count_1h', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('outgoing_transaction_count_1h', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('incoming_transaction_count_24h', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('outgoing_transaction_count_24h', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('total_inflow_24h', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('total_outflow_24h', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('estimated_remaining_amount', sa.Numeric(precision=15, scale=2), nullable=False, server_default=sa.text('0.00')),
        sa.Column('unique_incoming_sources_24h', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('linked_account_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('linked_case_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('historical_cashout_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('nearest_location_distance_km', sa.Numeric(precision=9, scale=3), nullable=False),
        sa.Column('hour_of_day', sa.Integer(), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('account_risk_score', sa.Numeric(precision=5, scale=4), nullable=False),
        sa.Column('prediction_mode', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_prediction_snapshots_case_id_complaints')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name=op.f('fk_prediction_snapshots_account_id_accounts')),
        sa.PrimaryKeyConstraint('snapshot_id', name=op.f('pk_prediction_snapshots'))
    )
    with op.batch_alter_table('prediction_snapshots', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_prediction_snapshots_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_snapshots_account_id'), ['account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_snapshots_prediction_timestamp'), ['prediction_timestamp'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_snapshots_prediction_mode'), ['prediction_mode'], unique=False)

    # 8. Location Candidates
    op.create_table(
        'location_candidates',
        sa.Column('candidate_id', sa.String(length=64), primary_key=True),
        sa.Column('snapshot_id', sa.String(length=64), nullable=False),
        sa.Column('location_id', sa.String(length=64), nullable=False),
        sa.Column('distance_from_account_km', sa.Numeric(precision=9, scale=3), nullable=False),
        sa.Column('historical_cashout_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('historical_case_count', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('historical_location_risk', sa.Numeric(precision=5, scale=4), nullable=False, server_default=sa.text('0.0000')),
        sa.Column('candidate_rank_reference', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['snapshot_id'], ['prediction_snapshots.snapshot_id'], name=op.f('fk_location_candidates_snapshot_id_prediction_snapshots')),
        sa.ForeignKeyConstraint(['location_id'], ['locations.location_id'], name=op.f('fk_location_candidates_location_id_locations')),
        sa.PrimaryKeyConstraint('candidate_id', name=op.f('pk_location_candidates'))
    )
    with op.batch_alter_table('location_candidates', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_location_candidates_snapshot_id'), ['snapshot_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_location_candidates_location_id'), ['location_id'], unique=False)

    # 9. Case Relationships
    op.create_table(
        'case_relationships',
        sa.Column('relationship_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=False),
        sa.Column('related_case_id', sa.String(length=64), nullable=False),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('relationship_type', sa.String(length=64), nullable=False),
        sa.Column('shared_transaction_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('shared_account_count', sa.Integer(), nullable=False, server_default=sa.text('1')),
        sa.Column('relationship_created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_case_relationships_case_id_complaints')),
        sa.ForeignKeyConstraint(['related_case_id'], ['complaints.case_id'], name=op.f('fk_case_relationships_related_case_id_complaints')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name=op.f('fk_case_relationships_account_id_accounts')),
        sa.PrimaryKeyConstraint('relationship_id', name=op.f('pk_case_relationships'))
    )
    with op.batch_alter_table('case_relationships', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_case_relationships_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_case_relationships_related_case_id'), ['related_case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_case_relationships_account_id'), ['account_id'], unique=False)

    # 10. Case Features
    op.create_table(
        'case_features',
        sa.Column('case_id', sa.String(length=64), primary_key=True),
        sa.Column('fraud_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('complaint_delay_minutes', sa.Integer(), nullable=False),
        sa.Column('transaction_count', sa.Integer(), nullable=False),
        sa.Column('unique_account_count', sa.Integer(), nullable=False),
        sa.Column('network_depth', sa.Integer(), nullable=False),
        sa.Column('network_branching_factor', sa.Numeric(precision=7, scale=3), nullable=False),
        sa.Column('cashout_count', sa.Integer(), nullable=False),
        sa.Column('total_cashout_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('distinct_cashout_locations', sa.Integer(), nullable=False),
        sa.Column('average_transaction_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('max_transaction_amount', sa.Numeric(precision=15, scale=2), nullable=False),
        sa.Column('synthetic_pattern_type', sa.String(length=64), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_case_features_case_id_complaints')),
        sa.PrimaryKeyConstraint('case_id', name=op.f('pk_case_features'))
    )

    # 11. Investigator Actions (Decision Support & Audit Log)
    op.create_table(
        'investigator_actions',
        sa.Column('action_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=False),
        sa.Column('action_type', sa.String(length=64), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('performed_by', sa.String(length=128), nullable=False, server_default='investigator_default'),
        sa.Column('action_status', sa.String(length=32), nullable=False, server_default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_investigator_actions_case_id_complaints')),
        sa.PrimaryKeyConstraint('action_id', name=op.f('pk_investigator_actions'))
    )
    with op.batch_alter_table('investigator_actions', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_investigator_actions_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_investigator_actions_action_type'), ['action_type'], unique=False)

    # 12. Prediction Ground Truth (Isolated Evaluation Table)
    op.create_table(
        'prediction_ground_truth',
        sa.Column('ground_truth_id', sa.String(length=64), primary_key=True),
        sa.Column('snapshot_id', sa.String(length=64), nullable=False),
        sa.Column('actual_next_cashout_event_id', sa.String(length=64), nullable=True),
        sa.Column('actual_next_location_id', sa.String(length=64), nullable=True),
        sa.Column('actual_next_cashout_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_minutes_until_cashout', sa.Integer(), nullable=True),
        sa.Column('actual_cashout_amount', sa.Numeric(precision=15, scale=2), nullable=True),
        sa.Column('has_future_cashout', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('evaluation_status', sa.String(length=64), nullable=False),
        sa.ForeignKeyConstraint(['snapshot_id'], ['prediction_snapshots.snapshot_id'], name=op.f('fk_prediction_ground_truth_snapshot_id_prediction_snapshots')),
        sa.ForeignKeyConstraint(['actual_next_cashout_event_id'], ['cashout_events.cashout_event_id'], name=op.f('fk_prediction_ground_truth_actual_next_cashout_event_id_cashout_events')),
        sa.ForeignKeyConstraint(['actual_next_location_id'], ['locations.location_id'], name=op.f('fk_prediction_ground_truth_actual_next_location_id_locations')),
        sa.PrimaryKeyConstraint('ground_truth_id', name=op.f('pk_prediction_ground_truth'))
    )
    with op.batch_alter_table('prediction_ground_truth', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_prediction_ground_truth_snapshot_id'), ['snapshot_id'], unique=False)

    # 13. Prediction Records (Immutable ML Prediction Audit & Provenance)
    op.create_table(
        'prediction_records',
        sa.Column('prediction_id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), nullable=False),
        sa.Column('snapshot_id', sa.String(length=64), nullable=True),
        sa.Column('account_id', sa.String(length=64), nullable=False),
        sa.Column('prediction_timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('occurrence_probability', sa.Float(), nullable=False),
        sa.Column('predicted_occurrence', sa.Boolean(), nullable=False),
        sa.Column('risk_tier', sa.String(length=32), nullable=False),
        sa.Column('top_location_id', sa.String(length=64), nullable=True),
        sa.Column('top_location_name', sa.String(length=128), nullable=True),
        sa.Column('top_location_distance_km', sa.Float(), nullable=True),
        sa.Column('estimated_minutes_until_cashout', sa.Float(), nullable=True),
        sa.Column('timing_window_low_minutes', sa.Float(), nullable=True),
        sa.Column('timing_window_high_minutes', sa.Float(), nullable=True),
        sa.Column('features_used_json', sa.Text(), nullable=False),
        sa.Column('occurrence_details_json', sa.Text(), nullable=False),
        sa.Column('location_ranking_json', sa.Text(), nullable=False),
        sa.Column('timing_details_json', sa.Text(), nullable=False),
        sa.Column('explanation_json', sa.Text(), nullable=False),
        sa.Column('model_metadata_json', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['case_id'], ['complaints.case_id'], name=op.f('fk_prediction_records_case_id_complaints')),
        sa.ForeignKeyConstraint(['snapshot_id'], ['prediction_snapshots.snapshot_id'], name=op.f('fk_prediction_records_snapshot_id_prediction_snapshots')),
        sa.ForeignKeyConstraint(['account_id'], ['accounts.account_id'], name=op.f('fk_prediction_records_account_id_accounts')),
        sa.ForeignKeyConstraint(['top_location_id'], ['locations.location_id'], name=op.f('fk_prediction_records_top_location_id_locations')),
        sa.PrimaryKeyConstraint('prediction_id', name=op.f('pk_prediction_records'))
    )
    with op.batch_alter_table('prediction_records', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_prediction_records_case_id'), ['case_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_records_snapshot_id'), ['snapshot_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_records_account_id'), ['account_id'], unique=False)
        batch_op.create_index(batch_op.f('ix_prediction_records_prediction_timestamp'), ['prediction_timestamp'], unique=False)


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table('prediction_records')
    op.drop_table('prediction_ground_truth')
    op.drop_table('investigator_actions')
    op.drop_table('case_features')
    op.drop_table('case_relationships')
    op.drop_table('location_candidates')
    op.drop_table('prediction_snapshots')
    op.drop_table('cashout_events')
    op.drop_table('transactions')
    op.drop_table('complaints')
    op.drop_table('account_labels')
    op.drop_table('accounts')
    op.drop_table('locations')
