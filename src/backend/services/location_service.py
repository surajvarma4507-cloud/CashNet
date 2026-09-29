"""Service layer for GIS Locations, ATMs, and branch infrastructure."""

import math
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from src.backend.db.models import CashoutEvent, Location
from src.backend.schemas import (
    LocationClusterListResponse,
    LocationClusterSummary,
    LocationDetail,
    LocationHotspotDetail,
    LocationHotspotListResponse,
    LocationListResponse,
    PaginationMeta,
)

CLUSTER_NAME_LOOKUP: Dict[str, str] = {
    "CLUSTER_MUM_BKC": "Bandra-Kurla Complex Financial Hub",
    "CLUSTER_MUM_SOUTH": "South Mumbai Nariman Point & Fort",
    "CLUSTER_MUM_ANDHERI": "Andheri Commercial & Industrial Area",
    "CLUSTER_MUM_BORIVALI": "Borivali-Kandivali Suburbs",
    "CLUSTER_MUM_THANE": "Thane West Commercial Corridor",
    "CLUSTER_MUM_VASHI": "Navi Mumbai Vashi-Belapur Nodes",
    "CLUSTER_MUM_KALYAN": "Kalyan-Dombivli Suburb Node",
    "CLUSTER_DEL_CP": "Connaught Place Central Business District",
    "CLUSTER_DEL_NEHRU": "Nehru Place Tech & Commercial Hub",
    "CLUSTER_DEL_KAROLBAGH": "Karol Bagh & Chandni Chowk Wholesale Market",
    "CLUSTER_DEL_GURUGRAM": "Cyber City & DLF Phase 2 Gurugram",
    "CLUSTER_DEL_NOIDA": "Sector 18 & Electronic City Noida",
    "CLUSTER_DEL_GHAZIABAD": "Ghaziabad Commercial Hub",
    "CLUSTER_DEL_FARIDABAD": "Faridabad Industrial Hub",
    "CLUSTER_BLR_KORAMANGALA": "Koramangala Commercial Tech Hub",
    "CLUSTER_BLR_INDIRANAGAR": "Indiranagar 100ft Road Corridor",
    "CLUSTER_BLR_WHITEFIELD": "Whitefield IT Park Cluster",
    "CLUSTER_BLR_ELEC_CITY": "Electronic City Phase 1 & 2",
    "CLUSTER_BLR_HSR": "HSR Layout & BTM Financial Cluster",
    "CLUSTER_BLR_MALLESHWARAM": "Malleshwaram & Rajajinagar Old Hub",
    "CLUSTER_HYD_HITEC": "Hitec City & Madhapur Cyberabad",
    "CLUSTER_HYD_BANJARA": "Banjara Hills & Jubilee Hills",
    "CLUSTER_HYD_SECUNDERABAD": "Secunderabad Railway Station & Market Hub",
    "CLUSTER_HYD_KUKATPALLY": "Kukatpally Housing Board Node",
    "CLUSTER_KOL_SALTLAKE": "Salt Lake Sector V Tech Center",
    "CLUSTER_KOL_PARKSTREET": "Park Street & BBD Bagh Central",
    "CLUSTER_KOL_NEWTOWN": "Rajarhat New Town Financial District",
    "CLUSTER_KOL_HOWRAH": "Howrah Railway & Wholesale Hub",
    "CLUSTER_PUN_HINJAWADI": "Hinjawadi Rajiv Gandhi Infotech Park",
    "CLUSTER_PUN_SHIVAJINAGAR": "Shivajinagar & FC Road Center",
    "CLUSTER_PUN_VIMANNAGAR": "Viman Nagar & Kharadi IT Hub",
    "CLUSTER_CHE_TNAGAR": "T. Nagar Commercial & Retail District",
    "CLUSTER_CHE_OMR": "Old Mahabalipuram Road IT Expressway",
    "CLUSTER_CHE_ANNANAGAR": "Anna Nagar Central Node",
    "CLUSTER_AHM_GIFTCITY": "GIFT City International Financial Centre",
    "CLUSTER_AHM_SGHIGHWAY": "SG Highway Corporate Corridor",
    "CLUSTER_JAI_MIROAD": "MI Road & C-Scheme Financial Center",
    "CLUSTER_LKO_HAZRATGANJ": "Hazratganj & Gomti Nagar Financial Node",
}


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculates great-circle distance between two GPS coordinates in kilometers."""
    r = 6371.0  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2.0) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class LocationService:
    """GIS terminal queries and spatial candidate searches."""

    @staticmethod
    def list_locations(
        db: Session,
        page: int = 1,
        page_size: int = 50,
        city: Optional[str] = None,
        region: Optional[str] = None,
        location_type: Optional[str] = None,
        area_cluster_id: Optional[str] = None,
        is_active: Optional[bool] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        radius_km: Optional[float] = None,
    ) -> LocationListResponse:
        """Paginated list of ATM and branch terminals with optional spatial proximity filtering."""
        query = db.query(Location)

        if city:
            query = query.filter(Location.city.ilike(f"%{city.strip()}%"))
        if region:
            query = query.filter(Location.region.ilike(f"%{region.strip()}%"))
        if location_type:
            query = query.filter(Location.location_type == location_type)
        if area_cluster_id:
            query = query.filter(Location.area_cluster_id == area_cluster_id)
        if is_active is not None:
            query = query.filter(Location.is_active == is_active)

        all_records = query.all()

        # Spatial radius filtering if requested
        if lat is not None and lon is not None and radius_km is not None:
            filtered_records = []
            for loc in all_records:
                dist = haversine_distance(lat, lon, float(loc.latitude), float(loc.longitude))
                if dist <= radius_km:
                    filtered_records.append((loc, dist))
            # Sort by distance
            filtered_records.sort(key=lambda x: x[1])
            all_records = [item[0] for item in filtered_records]

        total = len(all_records)
        total_pages = math.ceil(total / page_size) if total > 0 else 0

        # Apply pagination slicing
        offset = (page - 1) * page_size
        paged_items = all_records[offset : offset + page_size]

        return LocationListResponse(
            items=[LocationDetail.model_validate(loc) for loc in paged_items],
            pagination=PaginationMeta(
                total=total,
                page=page,
                page_size=page_size,
                total_pages=total_pages,
            ),
        )

    @staticmethod
    def get_location(db: Session, location_id: str) -> Optional[LocationDetail]:
        """Fetches a single location by ID."""
        location = db.query(Location).filter(Location.location_id == location_id).first()
        if not location:
            return None
        return LocationDetail.model_validate(location)

    @staticmethod
    def list_location_clusters(
        db: Session,
        city: Optional[str] = None,
    ) -> LocationClusterListResponse:
        """Aggregates active locations by spatial cluster with centroids and observed cashout metrics."""
        query = db.query(Location).filter(Location.is_active == True)
        if city:
            query = query.filter(Location.city.ilike(f"%{city.strip()}%"))

        locations = query.all()

        # Group locations by area_cluster_id
        cluster_map: Dict[str, List[Location]] = {}
        for loc in locations:
            cluster_id = loc.area_cluster_id or "CLUSTER_DEFAULT"
            cluster_map.setdefault(cluster_id, []).append(loc)

        # Get historical non-ground-truth cashout counts and sums per location
        # ANTI-LEAKAGE: strictly is_future_ground_truth == False
        cashout_stats = (
            db.query(
                CashoutEvent.location_id,
                func.count(CashoutEvent.cashout_event_id).label("cnt"),
                func.coalesce(func.sum(CashoutEvent.withdrawal_amount), 0).label("vol"),
            )
            .filter(CashoutEvent.is_future_ground_truth == False)
            .group_by(CashoutEvent.location_id)
            .all()
        )
        loc_cashout_map: Dict[str, Tuple[int, Decimal]] = {
            row[0]: (row[1], Decimal(str(row[2]))) for row in cashout_stats
        }

        cluster_summaries: List[LocationClusterSummary] = []
        for cluster_id, locs in sorted(cluster_map.items()):
            total_locs = len(locs)
            if total_locs == 0:
                continue

            # Compute centroid
            avg_lat = sum(float(l.latitude) for l in locs) / total_locs
            avg_lon = sum(float(l.longitude) for l in locs) / total_locs

            # Terminal type counts
            atm_count = sum(1 for l in locs if (l.location_type or "").lower() == "atm")
            branch_count = sum(1 for l in locs if (l.location_type or "").lower() == "branch")
            kiosk_count = sum(1 for l in locs if (l.location_type or "").lower() in ("kiosk", "csp"))

            # Aggregate cashouts
            cluster_cashout_cnt = 0
            cluster_cashout_vol = Decimal("0.00")
            for l in locs:
                if l.location_id in loc_cashout_map:
                    cnt, vol = loc_cashout_map[l.location_id]
                    cluster_cashout_cnt += cnt
                    cluster_cashout_vol += vol

            city_name = locs[0].city
            region_name = locs[0].region
            cluster_name = CLUSTER_NAME_LOOKUP.get(
                cluster_id,
                f"{city_name} {cluster_id.replace('CLUSTER_', '').replace('_', ' ').title()}",
            )

            cluster_summaries.append(
                LocationClusterSummary(
                    area_cluster_id=cluster_id,
                    cluster_name=cluster_name,
                    city=city_name,
                    region=region_name,
                    center_latitude=round(avg_lat, 6),
                    center_longitude=round(avg_lon, 6),
                    total_locations=total_locs,
                    atm_count=atm_count,
                    branch_count=branch_count,
                    kiosk_count=kiosk_count,
                    observed_cashout_events_count=cluster_cashout_cnt,
                    total_observed_cashout_volume=cluster_cashout_vol,
                )
            )

        return LocationClusterListResponse(
            total_clusters=len(cluster_summaries),
            items=cluster_summaries,
        )

    @staticmethod
    def list_location_hotspots(
        db: Session,
        city: Optional[str] = None,
        limit: int = 20,
        min_cashouts: int = 1,
    ) -> LocationHotspotListResponse:
        """Retrieves physical terminals with the highest observed historical cashout frequency."""
        # ANTI-LEAKAGE: strictly is_future_ground_truth == False
        cashout_query = (
            db.query(
                CashoutEvent.location_id,
                func.count(CashoutEvent.cashout_event_id).label("cashout_count"),
                func.coalesce(func.sum(CashoutEvent.withdrawal_amount), 0).label("total_volume"),
            )
            .filter(CashoutEvent.is_future_ground_truth == False)
            .group_by(CashoutEvent.location_id)
            .having(func.count(CashoutEvent.cashout_event_id) >= min_cashouts)
        )
        cashout_stats = cashout_query.all()
        loc_stats_map = {row[0]: (row[1], Decimal(str(row[2]))) for row in cashout_stats}

        loc_ids = list(loc_stats_map.keys())
        if not loc_ids:
            return LocationHotspotListResponse(total_hotspots=0, items=[])

        loc_query = db.query(Location).filter(Location.location_id.in_(loc_ids))
        if city:
            loc_query = loc_query.filter(Location.city.ilike(f"%{city.strip()}%"))

        locations = loc_query.all()
        hotspot_items: List[LocationHotspotDetail] = []
        for loc in locations:
            cnt, vol = loc_stats_map.get(loc.location_id, (0, Decimal("0.00")))
            if cnt < min_cashouts:
                continue

            # Risk level classification
            if cnt >= 5 or vol >= Decimal("500000.00"):
                risk_level = "high"
            elif cnt >= 2 or vol >= Decimal("100000.00"):
                risk_level = "elevated"
            else:
                risk_level = "moderate"

            hotspot_items.append(
                LocationHotspotDetail(
                    location_id=loc.location_id,
                    location_name=loc.location_name,
                    location_type=loc.location_type,
                    city=loc.city,
                    region=loc.region,
                    latitude=float(loc.latitude),
                    longitude=float(loc.longitude),
                    area_cluster_id=loc.area_cluster_id,
                    observed_cashout_count=cnt,
                    total_observed_cashout_volume=vol,
                    activity_risk_level=risk_level,
                )
            )

        # Sort by observed cashout count descending, then volume descending
        hotspot_items.sort(
            key=lambda x: (x.observed_cashout_count, x.total_observed_cashout_volume), reverse=True
        )
        paged_hotspots = hotspot_items[:limit]

        return LocationHotspotListResponse(
            total_hotspots=len(hotspot_items),
            items=paged_hotspots,
        )

