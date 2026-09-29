"""Location API endpoints for GIS terminal queries."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from src.backend.db.session import get_db
from src.backend.schemas import (
    LocationListResponse,
    LocationDetail,
    LocationClusterListResponse,
    LocationHotspotListResponse,
)
from src.backend.services.location_service import LocationService

router = APIRouter(prefix="/locations", tags=["Location GIS Terminals"])


@router.get(
    "",
    response_model=LocationListResponse,
    summary="List and search ATM/branch locations",
    description="Retrieve paginated list of physical terminals, ATMs, branches, and kiosks with filtering by city, region, type, cluster, or spatial radius search.",
)
def list_locations(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(50, ge=1, le=200, description="Items per page"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    region: Optional[str] = Query(None, description="Filter by state/region"),
    location_type: Optional[str] = Query(None, description="Filter by terminal type (e.g., atm, branch, kiosk)"),
    area_cluster_id: Optional[str] = Query(None, description="Filter by spatial area cluster ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    lat: Optional[float] = Query(None, description="Center latitude for spatial radius query"),
    lon: Optional[float] = Query(None, description="Center longitude for spatial radius query"),
    radius_km: Optional[float] = Query(None, ge=0.1, le=500.0, description="Radius in kilometers around (lat, lon)"),
    db: Session = Depends(get_db),
) -> LocationListResponse:
    return LocationService.list_locations(
        db=db,
        page=page,
        page_size=page_size,
        city=city,
        region=region,
        location_type=location_type,
        area_cluster_id=area_cluster_id,
        is_active=is_active,
        lat=lat,
        lon=lon,
        radius_km=radius_km,
    )


@router.get(
    "/nearby",
    response_model=LocationListResponse,
    summary="Nearby locations within radius",
    description="Find terminals within a radius of given lat/lon.",
)
def list_nearby_locations(
    latitude: float = Query(..., description="Center latitude"),
    longitude: float = Query(..., description="Center longitude"),
    radius_km: float = Query(5.0, ge=0.1, le=500.0, description="Radius in km"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    db: Session = Depends(get_db),
) -> LocationListResponse:
    return LocationService.list_locations(
        db=db,
        lat=latitude,
        lon=longitude,
        radius_km=radius_km,
        page=1,
        page_size=limit,
    )


@router.get(
    "/clusters",
    response_model=LocationClusterListResponse,
    summary="List location spatial clusters",
    description="Get aggregated spatial clusters with terminal counts and observed cashout history.",
)
def list_location_clusters(
    city: Optional[str] = Query(None, description="Filter by city"),
    db: Session = Depends(get_db),
) -> LocationClusterListResponse:
    return LocationService.list_location_clusters(db=db, city=city)


@router.get(
    "/hotspots",
    response_model=LocationHotspotListResponse,
    summary="List cash-out hotspot locations",
    description="Get high-frequency cashout terminals with historical (non-ground-truth) event counts.",
)
def list_location_hotspots(
    city: Optional[str] = Query(None, description="Filter by city"),
    limit: int = Query(20, ge=1, le=100, description="Max results"),
    min_cashouts: int = Query(1, ge=0, description="Minimum observed cashout events"),
    db: Session = Depends(get_db),
) -> LocationHotspotListResponse:
    return LocationService.list_location_hotspots(db=db, city=city, limit=limit, min_cashouts=min_cashouts)


@router.get(
    "/{location_id}",
    response_model=LocationDetail,
    summary="Get location by ID",
    description="Retrieve detailed information for a specific physical terminal.",
)
def get_location(
    location_id: str,
    db: Session = Depends(get_db),
) -> LocationDetail:
    location = LocationService.get_location(db=db, location_id=location_id)
    if not location:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Location with ID '{location_id}' was not found.",
        )
    return location
