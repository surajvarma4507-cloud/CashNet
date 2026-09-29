"""Account intelligence and multi-case money trail API endpoints."""

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.db.session import get_db
from src.backend.schemas import (
    AccountMoneyTrailsResponse,
    AccountNetworkResponse,
    
)
from src.backend.services.network_service import NetworkService
from src.backend.db.models import Account

router = APIRouter(prefix="/accounts", tags=["Account Network Intelligence"])


@router.get(
    "/{account_id}/network",
    response_model=AccountNetworkResponse,
    summary="Get account cross-case network profile",
    description="Retrieve multi-case intelligence for an account, including participating cases, total inflow/outflow, observed behavioral roles, and co-occurring counterparts.",
)
def get_account_network(
    account_id: str,
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> AccountNetworkResponse:
    try:
        net_profile = NetworkService.get_account_network(
            db=db,
            account_id=account_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not net_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found")
    return net_profile


@router.get(
    "/{account_id}/money-trails",
    response_model=AccountMoneyTrailsResponse,
    summary="Get account participation across case money trails",
    description="Retrieve all case money trails that an account has participated in, including hop level, role, and transaction volume per case.",
)
def get_account_money_trails(
    account_id: str,
    as_of: Optional[datetime] = Query(None, description="Optional point-in-time datetime filter (t <= as_of)"),
    snapshot_id: Optional[str] = Query(None, description="Optional prediction snapshot ID to resolve point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> AccountMoneyTrailsResponse:
    try:
        trails_profile = NetworkService.get_account_money_trails(
            db=db,
            account_id=account_id,
            as_of=as_of,
            snapshot_id=snapshot_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    if not trails_profile:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found")
    return trails_profile


@router.get(
    "/{account_id}",
    response_model=None,
    summary="Get account by ID",
    description="Retrieve account details by account_id",
)
def get_account_by_id(
    account_id: str,
    db: Session = Depends(get_db),
):
    account = db.query(Account).filter(Account.account_id == account_id).first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Account {account_id} not found")
    return {
        "account_id": account.account_id,
        "account_label": account.account_label,
        "account_type": account.account_type,
        "home_branch_id": account.home_branch_id,
        "home_city": account.home_city,
        "is_active": account.is_active,
    }
