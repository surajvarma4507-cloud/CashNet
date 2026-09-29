#!/usr/bin/env python3
"""CASHNET Evaluation Metrics Computation Script.

Computes Model A (Occurrence), Model B (Location Ranking), and Model C (Timing)
performance metrics on the held-out evaluation set.

Usage:
    python3 scripts/compute_evaluation_metrics.py

Output: JSON metrics report to stdout.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

import joblib
import numpy as np
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    mean_absolute_error,
    precision_score,
    recall_score,
    roc_auc_score,
)

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.backend.db.session import SessionLocal
from src.backend.db.models import (
    PredictionSnapshot,
    LocationCandidate,
    PredictionGroundTruth,
    Location,
)


def load_evaluation_data() -> pd.DataFrame:
    """Load evaluation ground truth with snapshots and candidates."""
    db = SessionLocal()
    try:
        # Join snapshots with ground truth and candidates
        query = db.query(
            PredictionSnapshot.case_id,
            PredictionSnapshot.snapshot_id,
            PredictionGroundTruth.has_future_cashout,
            PredictionGroundTruth.actual_next_location_id,
            PredictionGroundTruth.actual_minutes_until_cashout,
            PredictionGroundTruth.actual_cashout_amount,
            PredictionGroundTruth.evaluation_status,
        ).join(
            PredictionGroundTruth,
            PredictionSnapshot.snapshot_id == PredictionGroundTruth.snapshot_id
        ).filter(
            PredictionGroundTruth.evaluation_status.in_(['withdrawn_future', 'already_withdrawn_past'])
        )

        results = []
        for row in query.all():
            results.append({
                'case_id': row.case_id,
                'snapshot_id': row.snapshot_id,
                'has_future_cashout': row.has_future_cashout,
                'actual_next_location_id': row.actual_next_location_id,
                'actual_minutes_until_cashout': row.actual_minutes_until_cashout,
                'actual_cashout_amount': float(row.actual_cashout_amount) if row.actual_cashout_amount else None,
                'evaluation_status': row.evaluation_status,
            })

        return pd.DataFrame(results)
    finally:
        db.close()


def compute_occurrence_metrics(ground_truth: pd.DataFrame) -> Dict[str, Any]:
    """Compute occurrence classifier (Model A) metrics."""
    # Load Model A
    model_a_path = Path("models/occurrence_baseline.joblib")
    if not model_a_path.exists():
        return {"error": "Model A artifact not found"}

    model = joblib.load(model_a_path)

    # Load feature manifest
    manifest_path = Path("models/feature_manifest_used.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    feature_order = manifest['model_a_occurrence']['features']

    # Get features from database for evaluation set
    db = SessionLocal()
    try:
        # Get snapshots with all features
        snapshots = db.query(PredictionSnapshot).filter(
            PredictionSnapshot.snapshot_id.in_(ground_truth['snapshot_id'].tolist())
        ).all()

        snap_map = {s.snapshot_id: s for s in snapshots}

        # Build feature matrix in strict manifest order
        X = []
        y_list = []
        for _, row in ground_truth.iterrows():
            snap = snap_map.get(row['snapshot_id'])
            if snap is None:
                continue
            try:
                features = []
                for feat_name in feature_order:
                    val = getattr(snap, feat_name, None)
                    if val is None:
                        val = 0
                    features.append(float(val))
                X.append(features)
                y_list.append(int(row['has_future_cashout']))
            except Exception:
                continue

        if not X:
            return {"error": "No valid feature vectors extracted"}

        X = np.array(X)
        y_true = np.array(y_list)

        # Predict
        y_prob = model.predict_proba(X)[:, 1]
        y_pred = model.predict(X)

        # Metrics
        cm = confusion_matrix(y_true, y_pred)
        tn, fp, fn, tp = cm.ravel()

        metrics = {
            "model_name": "Model A: Occurrence Classifier",
            "model_artifact": "occurrence_baseline.joblib",
            "evaluation_sample_size": len(y_true),
            "threshold": 0.5,
            "accuracy": float(accuracy_score(y_true, y_pred)),
            "precision": float(precision_score(y_true, y_pred, zero_division=0)),
            "recall": float(recall_score(y_true, y_pred, zero_division=0)),
            "f1_score": float(f1_score(y_true, y_pred, zero_division=0)),
            "roc_auc": float(roc_auc_score(y_true, y_prob)),
            "pr_auc": float(average_precision_score(y_true, y_prob)),
            "brier_score": float(brier_score_loss(y_true, y_prob)),
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp),
            },
            "notes": "Metrics computed on evaluation set (ground_truth table). Predictions are advisory only."
        }

        return metrics
    finally:
        db.close()


def compute_location_ranking_metrics(ground_truth: pd.DataFrame) -> Dict[str, Any]:
    """Compute location ranking (Model B fallback) metrics."""
    db = SessionLocal()
    try:
        # Get candidates for each snapshot
        results = []

        for _, row in ground_truth.iterrows():
            snapshot_id = row['snapshot_id']
            actual_location = row['actual_next_location_id']

            if pd.isna(actual_location):
                continue

            # Get candidates ordered by distance (Model B fallback strategy)
            candidates = db.query(LocationCandidate).filter(
                LocationCandidate.snapshot_id == snapshot_id
            ).order_by(LocationCandidate.distance_from_account_km.asc()).all()

            if not candidates:
                continue

            # Check if actual is in top-1, top-3, top-5
            candidate_locations = [c.location_id for c in candidates]

            try:
                top1_acc = 1 if candidate_locations[0] == actual_location else 0
                top3_acc = 1 if actual_location in candidate_locations[:3] else 0
                top5_acc = 1 if actual_location in candidate_locations[:5] else 0

                results.append({
                    'snapshot_id': snapshot_id,
                    'actual': actual_location,
                    'top1': top1_acc,
                    'top3': top3_acc,
                    'top5': top5_acc,
                    'total_candidates': len(candidates),
                })
            except Exception:
                continue

        if not results:
            return {"error": "No valid location ranking results"}

        df = pd.DataFrame(results)

        metrics = {
            "model_name": "Model B: Distance-Based Fallback Ranker",
            "strategy": "distance_ascending",
            "evaluation_sample_size": len(df),
            "top1_accuracy": float(df['top1'].mean()),
            "top3_accuracy": float(df['top3'].mean()),
            "top5_accuracy": float(df['top5'].mean()),
            "average_candidates_per_case": float(df['total_candidates'].mean()),
            "notes": "Location ranking evaluated on evaluation set. Distance fallback is approved for operational use."
        }

        return metrics
    finally:
        db.close()


def compute_timing_metrics(ground_truth: pd.DataFrame) -> Dict[str, Any]:
    """Compute timing estimator (Model C) metrics."""
    # Filter to cases with actual timing
    with_timing = ground_truth[
        ground_truth['actual_minutes_until_cashout'].notna() &
        (ground_truth['evaluation_status'] == 'withdrawn_future')
    ]

    if len(with_timing) == 0:
        return {"error": "No timing targets available for evaluation"}

    # Load Model C
    model_c_path = Path("models/timing_baseline.joblib")
    if not model_c_path.exists():
        return {"error": "Model C artifact not found"}

    model = joblib.load(model_c_path)

    # Load feature manifest
    manifest_path = Path("models/feature_manifest_used.json")
    with open(manifest_path) as f:
        manifest = json.load(f)

    feature_order = manifest['model_a_occurrence']['features']

    # Get features from database
    db = SessionLocal()
    try:
        snap_map = {s.snapshot_id: s for s in db.query(PredictionSnapshot).filter(
            PredictionSnapshot.snapshot_id.in_(with_timing['snapshot_id'].tolist())
        ).all()}

        X = []
        y_list = []
        for _, row in with_timing.iterrows():
            snap = snap_map.get(row['snapshot_id'])
            if snap is None:
                continue
            features = []
            for feat_name in feature_order:
                val = getattr(snap, feat_name, None)
                if val is None:
                    val = 0
                features.append(float(val))
            X.append(features)
            y_list.append(float(row['actual_minutes_until_cashout']))

        if not X:
            return {"error": "No valid timing features extracted"}

        X = np.array(X)
        y_true = np.array(y_list)

        y_pred = model.predict(X)

        mae = mean_absolute_error(y_true, y_pred)

        # Simple baseline: predict median (approximately 95 min from uniform 10-180)
        baseline_mae = mean_absolute_error(y_true, np.full_like(y_true, 95))

        metrics = {
            "model_name": "Model C: Timing Regressor",
            "model_artifact": "timing_baseline.joblib",
            "evaluation_sample_size": len(y_true),
            "mae_minutes": float(mae),
            "baseline_mae_minutes": float(baseline_mae),
            "notes": "Timing model has high uncertainty due to uniform random delays in synthetic generator. Marked as experimental baseline."
        }

        return metrics
    finally:
        db.close()


def main():
    """Main evaluation computation."""
    print("Loading evaluation ground truth...", file=sys.stderr)
    ground_truth = load_evaluation_data()

    print(f"Loaded {len(ground_truth)} evaluation records", file=sys.stderr)

    results = {
        "generated_at": pd.Timestamp.now().isoformat(),
        "dataset_info": {
            "total_evaluation_records": len(ground_truth),
            "future_cashout_count": int(ground_truth['has_future_cashout'].sum()),
            "past_cashout_count": int((~ground_truth['has_future_cashout']).sum()),
        },
        "models": {}
    }

    # Compute each model's metrics
    print("Computing Model A (Occurrence) metrics...", file=sys.stderr)
    results["models"]["occurrence"] = compute_occurrence_metrics(ground_truth)

    print("Computing Model B (Location Ranking) metrics...", file=sys.stderr)
    results["models"]["location_ranking"] = compute_location_ranking_metrics(ground_truth)

    print("Computing Model C (Timing) metrics...", file=sys.stderr)
    results["models"]["timing"] = compute_timing_metrics(ground_truth)

    # Output JSON
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()