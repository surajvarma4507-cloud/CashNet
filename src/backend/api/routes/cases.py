"""Case, Complaint, and Money Trail API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.db.session import get_db
from src.backend.schemas import (
    CaseAccountListResponse,
    CaseDetailResponse,
    CaseGraphResponse,
    CaseListResponse,
    CaseNetworkResponse,
    InvestigatorActionCreate,
    InvestigatorActionDetail,
    MoneyTrailResponse,
    RelatedCaseListResponse,
    TransactionListResponse,
)
from src.backend.services.case_service import CaseService
from src.backend.services.money_trail_service import MoneyTrailService
from src.backend.services.network_service import NetworkService

router = APIRouter(prefix="/cases", tags=["Cases & Money Trails"])


@router.get(
    "",
    response_model=CaseListResponse,
    summary="List and filter cybercrime cases",
    description="Retrieve a paginated list of cybercrime complaints with filtering by status, fraud type, channel, amount range, date range, point-in-time as_of, and free-text search.",
)
def list_cases(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Number of items per page"),
    search: Optional[str] = Query(None, description="Search term for case ID, victim account, or description"),
    status: Optional[str] = Query(None, description="Filter by complaint status (e.g., registered, under_investigation, resolved)"),
    fraud_type: Optional[str] = Query(None, description="Filter by fraud typology (e.g., investment_scam, sextortion, digital_arrest)"),
    fraud_channel: Optional[str] = Query(None, description="Filter by fraud channel (e.g., UPI, IMPS, NEFT, AEPS)"),
    min_amount: Optional[float] = Query(None, ge=0, description="Minimum fraud amount in INR"),
    max_amount: Optional[float] = Query(None, ge=0, description="Maximum fraud amount in INR"),
    from_date: Optional[datetime] = Query(None, description="Filter complaints registered on or after this timestamp"),
    to_date: Optional[datetime] = Query(None, description="Filter complaints registered on or before this timestamp"),
    as_of: Optional[datetime] = Query(None, description="Point-in-time ISO timestamp filter (t <= as_of)"),
    order_by: str = Query("complaint_registered_at", description="Field to sort by (complaint_registered_at, fraud_occurred_at, fraud_amount)"),
    order_desc: bool = Query(True, description="Sort descending if true, ascending if false"),
    db: Session = Depends(get_db),
) -> CaseListResponse:
    return CaseService.list_cases(
        db=db,
        page=page,
        page_size=page_size,
        search=search,
        status=status,
        fraud_type=fraud_type,
        fraud_channel=fraud_channel,
        min_amount=min_amount,
        max_amount=max_amount,
        from_date=from_date,
        to_date=to_date,
        as_of=as_of,
        order_by=order_by,
        order_desc=order_desc,
    )


@router.get(
    "/{case_id}",
    response_model=CaseDetailResponse,
    summary="Get cybercrime case details",
    description="Retrieve complete dossier for a specific case with optional point-in-time reconstruction via as_of or prediction snapshot ID.",
)
def get_case(
    case_id: str,
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> CaseDetailResponse:
    try:
        case_data = CaseService.get_case(db, case_id=case_id, as_of=as_of, snapshot_id=snapshot_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not case_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found (or does not exist as of the specified time).",
        )
    return case_data


@router.get(
    "/{case_id}/transactions",
    response_model=TransactionListResponse,
    summary="Get case money trail transactions",
    description="Retrieve all financial transactions belonging to the case money trail in strict chronological order with hop relationships, location metadata, and point-in-time filtering.",
)
def get_case_transactions(
    case_id: str,
    fraud_linked_only: bool = Query(False, description="If true, return only transactions explicitly flagged as fraud money trail"),
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> TransactionListResponse:
    # Ensure case exists
    try:
        case_data = CaseService.get_case(db, case_id=case_id, as_of=as_of, snapshot_id=snapshot_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not case_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return CaseService.get_case_transactions(
        db,
        case_id=case_id,
        fraud_linked_only=fraud_linked_only,
        as_of=as_of,
        snapshot_id=snapshot_id,
    )


@router.get(
    "/{case_id}/accounts",
    response_model=CaseAccountListResponse,
    summary="Get accounts involved in case money trail",
    description="Retrieve all unique accounts involved in the case money trail (victim, mule hop 1, mule hop 2, cashout nodes) along with transaction aggregates, supervised mule labels, and point-in-time filtering.",
)
def get_case_accounts(
    case_id: str,
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> CaseAccountListResponse:
    try:
        accounts_data = CaseService.get_case_accounts(
            db,
            case_id=case_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not accounts_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return accounts_data


@router.post(
    "/{case_id}/actions",
    response_model=InvestigatorActionDetail,
    status_code=status.HTTP_201_CREATED,
    summary="Record investigator decision action",
    description="Log an investigator decision support action, freeze order dispatch, tactical alert, or review note into the immutable audit trail.",
)
def create_case_action(
    case_id: str,
    action_in: InvestigatorActionCreate,
    db: Session = Depends(get_db),
) -> InvestigatorActionDetail:
    action = CaseService.add_investigator_action(db, case_id=case_id, action_in=action_in)
    if not action:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return action


@router.get(
    "/{case_id}/money-trail",
    response_model=MoneyTrailResponse,
    summary="Get reconstructed multi-hop money trail",
    description="Trace transaction flow from the victim account across multi-hop layered accounts into a directed graph and chronological ledger with anomaly detection.",
)
def get_case_money_trail(
    case_id: str,
    fraud_linked_only: bool = Query(False, description="If true, return only transactions flagged as fraud money trail"),
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> MoneyTrailResponse:
    try:
        trail = MoneyTrailService.reconstruct_money_trail(
            db=db,
            case_id=case_id,
            fraud_linked_only=fraud_linked_only,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not trail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return trail


@router.get(
    "/{case_id}/graph",
    response_model=CaseGraphResponse,
    summary="Get case graph visualization representation",
    description="Retrieve graph nodes, directed edges, and structural topological metrics (density, components, cycles) formatted for UI graph renderers.",
)
def get_case_graph(
    case_id: str,
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> CaseGraphResponse:
    try:
        graph = MoneyTrailService.get_case_graph(
            db=db,
            case_id=case_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not graph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return graph


@router.get(
    "/{case_id}/network",
    response_model=CaseNetworkResponse,
    summary="Get cross-case financial network intelligence",
    description="Identify shared mule accounts, connected syndicate cases, hub accounts, and cluster metrics across the observed financial transaction network.",
)
def get_case_network(
    case_id: str,
    max_depth: int = Query(2, ge=1, le=5, description="Graph traversal depth for syndicate discovery"),
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> CaseNetworkResponse:
    try:
        network = NetworkService.get_case_network(
            db=db,
            case_id=case_id,
            max_depth=max_depth,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not network:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return network


@router.get(
    "/{case_id}/related-cases",
    response_model=RelatedCaseListResponse,
    summary="List related cases connected by shared financial infrastructure",
    description="Retrieve a paginated collection of related cybercrime cases linked by shared intermediary or cashout accounts with evidence.",
)
def get_related_cases(
    case_id: str,
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> RelatedCaseListResponse:
    try:
        related = NetworkService.get_related_cases(
            db=db,
            case_id=case_id,
            page=page,
            page_size=page_size,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    if not related:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Case with ID '{case_id}' was not found.",
        )
    return related

