"""Location Generator for CASHNET Synthetic Financial Engine.

Generates realistic synthetic Indian ATM, branch, CSP kiosk, and merchant POS locations
clustered across major Indian metropolitan areas (MMR, NCR, Bengaluru, Hyderabad, Kolkata, Pune, Chennai, etc.).
"""

import math
import random
from datetime import datetime, timezone
from typing import Any, Dict, List

from ..config import INDIAN_METRO_CLUSTERS, LOCATION_TYPES, GenerationConfig


def generate_locations(config: GenerationConfig) -> List[Dict[str, Any]]:
    """Generates a reproducible list of synthetic Indian financial/ATM locations.

    Args:
        config: Generation configuration containing random seed and location count.

    Returns:
        List of location dictionary records matching the schema.
    """
    rng = random.Random(config.seed)
    num_locations = config.num_locations
    locations: List[Dict[str, Any]] = []

    clusters = INDIAN_METRO_CLUSTERS
    num_clusters = len(clusters)

    # Distribute locations among clusters
    locs_per_cluster = math.ceil(num_locations / num_clusters)

    counter = 1
    for cluster_idx, cluster in enumerate(clusters):
        for _ in range(locs_per_cluster):
            if counter > num_locations:
                break

            loc_id = f"SYNTH_LOC_{counter:04d}"
            loc_type = rng.choices(
                LOCATION_TYPES,
                weights=[0.68, 0.14, 0.10, 0.08],  # 68% ATMs, 14% branches, 10% CSPs, 8% POS
                k=1
            )[0]

            # Generate realistic jitter within cluster radius (1 degree lat ~= 111 km)
            radius_deg = (cluster.radius_km / 111.0)
            angle = rng.uniform(0, 2 * math.pi)
            distance = rng.uniform(0, radius_deg)
            lat = round(cluster.center_lat + distance * math.sin(angle), 6)
            lon = round(cluster.center_lon + distance * math.cos(angle), 6)

            # Ensure strict bounding within India
            lat = max(6.5, min(37.5, lat))
            lon = max(68.5, min(97.5, lon))

            # Type prefix
            type_abbr = {
                "atm": "ATM",
                "branch": "BRN",
                "csp_kiosk": "CSP",
                "pos_merchant": "POS"
            }.get(loc_type, "ATM")

            city_clean = cluster.city.replace(" ", "")[:3].upper()
            cluster_short = cluster.cluster_id.replace("CLUSTER_", "")[:6]
            loc_name = f"SYNTH_{type_abbr}_{city_clean}_{cluster_short}_{counter:04d}"

            # 98% active, 2% temporarily inactive / maintenance
            is_active = rng.random() < 0.98

            created_at_dt = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

            record = {
                "location_id": loc_id,
                "location_name": loc_name,
                "location_type": loc_type,
                "city": cluster.city,
                "region": cluster.region,
                "latitude": lat,
                "longitude": lon,
                "area_cluster_id": cluster.cluster_id,
                "synthetic_location_group": cluster.zone,
                "is_active": is_active,
                "created_at": created_at_dt.strftime("%Y-%m-%dT%H:%M:%SZ"),
            }
            locations.append(record)
            counter += 1

    return locations
