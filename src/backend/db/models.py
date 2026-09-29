"""SQLAlchemy models for CASHNET core relational entities."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    event,
    false,
    true,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.backend.db.base import Base


class Location(Base):
    """Geographic ATM, branch, and kiosk physical terminal metadata."""

    __tablename__ = "locations"

    location_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    location_name: Mapped[str] = mapped_column(String(128), nullable=False)
    location_type: Mapped[str] = mapped_column(String(32), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    latitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    longitude: Mapped[float] = mapped_column(Numeric(9, 6), nullable=False)
    area_cluster_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    synthetic_location_group: Mapped[str] = mapped_column(String(64), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=true(), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    accounts: Mapped[List["Account"]] = relationship("Account", back_populates="home_location")


class Account(Base):
    """Synthetic bank and digital wallet accounts."""

    __tablename__ = "accounts"

    account_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    account_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    account_opened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    account_age_days: Mapped[int] = mapped_column(Integer, nullable=False)
    home_location_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=True, index=True)
    account_status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    baseline_transaction_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    baseline_monthly_inflow: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    baseline_monthly_outflow: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    synthetic_profile_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    home_location: Mapped[Optional["Location"]] = relationship("Location", back_populates="accounts")
    label: Mapped[Optional["AccountLabel"]] = relationship("AccountLabel", back_populates="account", uselist=False)


class Complaint(Base):
    """Cybercrime complaints registered with NCRP / 1930 incident response."""

    __tablename__ = "complaints"

    case_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    victim_account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    fraud_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fraud_channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    fraud_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    fraud_currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    fraud_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    complaint_registered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    complaint_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    victim_location_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=True, index=True)
    initial_transaction_id: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    complaint_status: Mapped[str] = mapped_column(String(32), default="registered", nullable=False, index=True)
    synthetic_description: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    victim_account: Mapped["Account"] = relationship("Account", foreign_keys=[victim_account_id])
    victim_location: Mapped[Optional["Location"]] = relationship("Location", foreign_keys=[victim_location_id])
    transactions: Mapped[List["Transaction"]] = relationship("Transaction", back_populates="complaint", cascade="all, delete-orphan")
    cashouts: Mapped[List["CashoutEvent"]] = relationship("CashoutEvent", back_populates="complaint", cascade="all, delete-orphan")
    snapshots: Mapped[List["PredictionSnapshot"]] = relationship("PredictionSnapshot", back_populates="complaint", cascade="all, delete-orphan")
    features: Mapped[Optional["CaseFeature"]] = relationship("CaseFeature", back_populates="complaint", uselist=False, cascade="all, delete-orphan")
    actions: Mapped[List["InvestigatorAction"]] = relationship("InvestigatorAction", back_populates="complaint", cascade="all, delete-orphan")


class Transaction(Base):
    """Financial money trail transfers, deposits, and cashout settlements."""

    __tablename__ = "transactions"

    transaction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=True, index=True)
    from_account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    to_account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(8), default="INR", nullable=False)
    transaction_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    channel: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    transaction_status: Mapped[str] = mapped_column(String(32), default="completed", nullable=False)
    initiated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    location_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=True, index=True)
    is_fraud_linked: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False, index=True)
    synthetic_event_group_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped[Optional["Complaint"]] = relationship("Complaint", back_populates="transactions")
    from_account: Mapped["Account"] = relationship("Account", foreign_keys=[from_account_id])
    to_account: Mapped["Account"] = relationship("Account", foreign_keys=[to_account_id])
    location: Mapped[Optional["Location"]] = relationship("Location", foreign_keys=[location_id])


class CashoutEvent(Base):
    """Physical ATM / branch cashout milestones."""

    __tablename__ = "cashout_events"

    cashout_event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=False, index=True)
    transaction_id: Mapped[str] = mapped_column(String(64), ForeignKey("transactions.transaction_id"), nullable=False, index=True)
    withdrawal_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    cashout_occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    minutes_since_previous_transaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_future_ground_truth: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    synthetic_event_group_id: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="cashouts")
    account: Mapped["Account"] = relationship("Account")
    location: Mapped["Location"] = relationship("Location")
    transaction: Mapped["Transaction"] = relationship("Transaction")


class AccountLabel(Base):
    """Supervised mule labels and behavioral roles for model training."""

    __tablename__ = "account_labels"

    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), primary_key=True)
    is_synthetic_mule: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    synthetic_behaviour_type: Mapped[str] = mapped_column(String(64), nullable=False)
    label_generation_reason: Mapped[str] = mapped_column(String(255), nullable=False)
    label_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    account: Mapped["Account"] = relationship("Account", back_populates="label")


class PredictionSnapshot(Base):
    """Point-in-time investigator state vector at complaint registration timestamp."""

    __tablename__ = "prediction_snapshots"

    snapshot_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    complaint_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    minutes_since_last_transaction: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    incoming_transaction_count_1h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outgoing_transaction_count_1h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    incoming_transaction_count_24h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    outgoing_transaction_count_24h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_inflow_24h: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    total_outflow_24h: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    estimated_remaining_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0.00"), nullable=False)
    unique_incoming_sources_24h: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    linked_account_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    linked_case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    historical_cashout_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    nearest_location_distance_km: Mapped[Decimal] = mapped_column(Numeric(9, 3), nullable=False)
    hour_of_day: Mapped[int] = mapped_column(Integer, nullable=False)
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)
    account_risk_score: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    prediction_mode: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="snapshots")
    candidates: Mapped[List["LocationCandidate"]] = relationship("LocationCandidate", back_populates="snapshot", cascade="all, delete-orphan")


class LocationCandidate(Base):
    """Spatial ATM candidate ranking pairs for tactical LEA dispatch."""

    __tablename__ = "location_candidates"

    candidate_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), ForeignKey("prediction_snapshots.snapshot_id"), nullable=False, index=True)
    location_id: Mapped[str] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=False, index=True)
    distance_from_account_km: Mapped[Decimal] = mapped_column(Numeric(9, 3), nullable=False)
    historical_cashout_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    historical_case_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    historical_location_risk: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0.0000"), nullable=False)
    candidate_rank_reference: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    snapshot: Mapped["PredictionSnapshot"] = relationship("PredictionSnapshot", back_populates="candidates")
    location: Mapped["Location"] = relationship("Location")


class CaseRelationship(Base):
    """Network co-occurrence links between cross-case shared mules."""

    __tablename__ = "case_relationships"

    relationship_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    related_case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(64), nullable=False)
    shared_transaction_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    shared_account_count: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    relationship_created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)


class CaseFeature(Base):
    """Forensic vectors and graph topological features computed at complaint time."""

    __tablename__ = "case_features"

    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), primary_key=True)
    fraud_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    complaint_delay_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    transaction_count: Mapped[int] = mapped_column(Integer, nullable=False)
    unique_account_count: Mapped[int] = mapped_column(Integer, nullable=False)
    network_depth: Mapped[int] = mapped_column(Integer, nullable=False)
    network_branching_factor: Mapped[Decimal] = mapped_column(Numeric(7, 3), nullable=False)
    cashout_count: Mapped[int] = mapped_column(Integer, nullable=False)
    total_cashout_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    distinct_cashout_locations: Mapped[int] = mapped_column(Integer, nullable=False)
    average_transaction_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    max_transaction_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    synthetic_pattern_type: Mapped[str] = mapped_column(String(64), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="features")


class InvestigatorAction(Base):
    """Investigator decision support audit events, freeze orders, and dispatched alerts."""

    __tablename__ = "investigator_actions"

    action_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    action_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # e.g., 'dispatch_alert', 'account_freeze', 'note_added', 'review_completed'
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    performed_by: Mapped[str] = mapped_column(String(128), nullable=False, default="investigator_default")
    action_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint", back_populates="actions")


@event.listens_for(InvestigatorAction, "before_update")
def receive_investigator_action_before_update(mapper, connection, target):
    raise PermissionError("InvestigatorAction records are append-only and cannot be modified.")


@event.listens_for(InvestigatorAction, "before_delete")
def receive_investigator_action_before_delete(mapper, connection, target):
    raise PermissionError("InvestigatorAction records are append-only and cannot be deleted.")


class PredictionGroundTruth(Base):
    """Isolated evaluation ground truth table (Strictly separated from ordinary case / prediction APIs)."""

    __tablename__ = "prediction_ground_truth"

    ground_truth_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    snapshot_id: Mapped[str] = mapped_column(String(64), ForeignKey("prediction_snapshots.snapshot_id"), nullable=False, index=True)
    actual_next_cashout_event_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("cashout_events.cashout_event_id"), nullable=True)
    actual_next_location_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=True)
    actual_next_cashout_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    actual_minutes_until_cashout: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    actual_cashout_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(15, 2), nullable=True)
    has_future_cashout: Mapped[bool] = mapped_column(Boolean, default=False, server_default=false(), nullable=False)
    evaluation_status: Mapped[str] = mapped_column(String(64), nullable=False)


class PredictionRecord(Base):
    """Immutable audit record of executed ML prediction runs and decision support advisories."""

    __tablename__ = "prediction_records"

    prediction_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    case_id: Mapped[str] = mapped_column(String(64), ForeignKey("complaints.case_id"), nullable=False, index=True)
    snapshot_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("prediction_snapshots.snapshot_id"), nullable=True, index=True)
    account_id: Mapped[str] = mapped_column(String(64), ForeignKey("accounts.account_id"), nullable=False, index=True)
    prediction_timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Model A: Occurrence
    occurrence_probability: Mapped[float] = mapped_column(Float, nullable=False)
    predicted_occurrence: Mapped[bool] = mapped_column(Boolean, nullable=False)
    risk_tier: Mapped[str] = mapped_column(String(32), nullable=False)

    # Model B: Location Ranking (Top 1)
    top_location_id: Mapped[Optional[str]] = mapped_column(String(64), ForeignKey("locations.location_id"), nullable=True)
    top_location_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    top_location_distance_km: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Model C: Timing
    estimated_minutes_until_cashout: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timing_window_low_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    timing_window_high_minutes: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Full JSON payloads for audit and reproducibility
    features_used_json: Mapped[str] = mapped_column(Text, nullable=False)
    occurrence_details_json: Mapped[str] = mapped_column(Text, nullable=False)
    location_ranking_json: Mapped[str] = mapped_column(Text, nullable=False)
    timing_details_json: Mapped[str] = mapped_column(Text, nullable=False)
    explanation_json: Mapped[str] = mapped_column(Text, nullable=False)
    model_metadata_json: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    # Relationships
    complaint: Mapped["Complaint"] = relationship("Complaint")
    account: Mapped["Account"] = relationship("Account")
    snapshot: Mapped[Optional["PredictionSnapshot"]] = relationship("PredictionSnapshot")
    top_location: Mapped[Optional["Location"]] = relationship("Location")

