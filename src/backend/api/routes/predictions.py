"""Prediction and Investigator Decision Support API Endpoints."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.db.session import get_db
from src.backend.schemas import (
    CasePredictionHistoryResponse,
    PredictionDetailResponse,
    PredictionTriggerRequest,
)
from src.backend.services.prediction_service import PredictionService

router = APIRouter(tags=["ML Predictions & Decision Support"])


@router.post(
    "/cases/{case_id}/predictions",
    response_model=PredictionDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Trigger ML cash-out prediction and decision support advisory for a case",
    description=(
        "Executes approved Model A occurrence classifier, verified Model B fallback distance location ranking, "
        "and Model C timing baseline with comprehensive feature provenance and law enforcement decision support narrative."
    ),
)
def trigger_case_prediction(
    case_id: str,
    payload: Optional[PredictionTriggerRequest] = None,
    db: Session = Depends(get_db),
) -> PredictionDetailResponse:
    """Triggers ML prediction execution for a specific case."""
    try:
        return PredictionService.execute_prediction(db=db, case_id=case_id, req=payload)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Prediction execution failed: {str(e)}",
        )


@router.get(
    "/cases/{case_id}/predictions",
    response_model=CasePredictionHistoryResponse,
    summary="Get prediction execution history for a case",
    description="Retrieve paginated historical prediction runs and decision support advisories generated for a case.",
)
def list_case_predictions(
    case_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
) -> CasePredictionHistoryResponse:
    """Lists historical prediction records for a case."""
    history = PredictionService.list_case_predictions(db=db, case_id=case_id, page=page, page_size=page_size)
    if history is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return history


@router.get(
    "/predictions/{prediction_id}",
    response_model=PredictionDetailResponse,
    summary="Get prediction audit details by ID",
    description="Retrieve immutable prediction execution record, exact feature inputs, model metadata, and advisory explanation.",
)
def get_prediction_by_id(
    prediction_id: str,
    db: Session = Depends(get_db),
) -> PredictionDetailResponse:
    """Fetches a stored prediction record by prediction ID."""
    record = PredictionService.get_prediction(db=db, prediction_id=prediction_id)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prediction with ID '{prediction_id}' was not found.",
        )
    return record
