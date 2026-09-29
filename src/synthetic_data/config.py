"""CASHNET Synthetic Data Generator Configuration & Constants.

Defines schemas, profiles, Indian geographic clusters, and parameters for
generating synthetic cybercrime financial trails and ground truth.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class GeographicCluster:
    """Represents a metropolitan geographic cluster in India."""
    cluster_id: str
    cluster_name: str
    city: str
    region: str
    zone: str  # e.g., 'WEST_ZONE_METRO', 'NORTH_ZONE_METRO'
    center_lat: float
    center_lon: float
    radius_km: float


INDIAN_METRO_CLUSTERS: List[GeographicCluster] = [
    # Mumbai Metropolitan Region (MMR) - West Zone
    GeographicCluster("CLUSTER_MUM_BKC", "Bandra-Kurla Complex Financial Hub", "Mumbai", "Maharashtra", "WEST_ZONE_METRO", 19.0674, 72.8687, 4.0),
    GeographicCluster("CLUSTER_MUM_SOUTH", "South Mumbai Nariman Point & Fort", "Mumbai", "Maharashtra", "WEST_ZONE_METRO", 18.9280, 72.8330, 5.0),
    GeographicCluster("CLUSTER_MUM_ANDHERI", "Andheri Commercial & Industrial Area", "Mumbai", "Maharashtra", "WEST_ZONE_METRO", 19.1197, 72.8464, 6.0),
    GeographicCluster("CLUSTER_MUM_BORIVALI", "Borivali-Kandivali Suburbs", "Mumbai", "Maharashtra", "WEST_ZONE_METRO", 19.2307, 72.8567, 5.0),
    GeographicCluster("CLUSTER_MUM_THANE", "Thane West Commercial Corridor", "Thane", "Maharashtra", "WEST_ZONE_METRO", 19.2183, 72.9781, 6.0),
    GeographicCluster("CLUSTER_MUM_VASHI", "Navi Mumbai Vashi-Belapur Nodes", "Navi Mumbai", "Maharashtra", "WEST_ZONE_METRO", 19.0771, 72.9986, 7.0),
    GeographicCluster("CLUSTER_MUM_KALYAN", "Kalyan-Dombivli Suburb Node", "Kalyan", "Maharashtra", "WEST_ZONE_METRO", 19.2403, 73.1305, 6.0),

    # Delhi NCR - North Zone
    GeographicCluster("CLUSTER_DEL_CP", "Connaught Place Central Business District", "New Delhi", "Delhi NCR", "NORTH_ZONE_METRO", 28.6315, 77.2167, 4.0),
    GeographicCluster("CLUSTER_DEL_NEHRU", "Nehru Place Tech & Commercial Hub", "New Delhi", "Delhi NCR", "NORTH_ZONE_METRO", 28.5494, 77.2536, 4.0),
    GeographicCluster("CLUSTER_DEL_KAROLBAGH", "Karol Bagh & Chandni Chowk Wholesale Market", "New Delhi", "Delhi NCR", "NORTH_ZONE_METRO", 28.6514, 77.1907, 5.0),
    GeographicCluster("CLUSTER_DEL_GURUGRAM", "Cyber City & DLF Phase 2 Gurugram", "Gurugram", "Haryana", "NORTH_ZONE_METRO", 28.4950, 77.0890, 7.0),
    GeographicCluster("CLUSTER_DEL_NOIDA", "Sector 18 & Electronic City Noida", "Noida", "Uttar Pradesh", "NORTH_ZONE_METRO", 28.5708, 77.3271, 6.0),
    GeographicCluster("CLUSTER_DEL_GHAZIABAD", "Ghaziabad Commercial Hub", "Ghaziabad", "Uttar Pradesh", "NORTH_ZONE_METRO", 28.6692, 77.4538, 6.0),
    GeographicCluster("CLUSTER_DEL_FARIDABAD", "Faridabad Industrial Hub", "Faridabad", "Haryana", "NORTH_ZONE_METRO", 28.4089, 77.3178, 6.0),

    # Bengaluru - South Zone
    GeographicCluster("CLUSTER_BLR_KORAMANGALA", "Koramangala Commercial Tech Hub", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 12.9352, 77.6245, 4.0),
    GeographicCluster("CLUSTER_BLR_INDIRANAGAR", "Indiranagar 100ft Road Corridor", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 12.9784, 77.6408, 4.0),
    GeographicCluster("CLUSTER_BLR_WHITEFIELD", "Whitefield IT Park Cluster", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 12.9698, 77.7500, 6.0),
    GeographicCluster("CLUSTER_BLR_ELEC_CITY", "Electronic City Phase 1 & 2", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 12.8452, 77.6602, 6.0),
    GeographicCluster("CLUSTER_BLR_HSR", "HSR Layout & BTM Financial Cluster", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 12.9121, 77.6446, 4.0),
    GeographicCluster("CLUSTER_BLR_MALLESHWARAM", "Malleshwaram & Rajajinagar Old Hub", "Bengaluru", "Karnataka", "SOUTH_ZONE_METRO", 13.0031, 77.5643, 5.0),

    # Hyderabad - South Zone
    GeographicCluster("CLUSTER_HYD_HITEC", "Hitec City & Madhapur Cyberabad", "Hyderabad", "Telangana", "SOUTH_ZONE_METRO", 17.4435, 78.3772, 5.0),
    GeographicCluster("CLUSTER_HYD_BANJARA", "Banjara Hills & Jubilee Hills", "Hyderabad", "Telangana", "SOUTH_ZONE_METRO", 17.4156, 78.4350, 5.0),
    GeographicCluster("CLUSTER_HYD_SECUNDERABAD", "Secunderabad Railway Station & Market Hub", "Secunderabad", "Telangana", "SOUTH_ZONE_METRO", 17.4399, 78.4983, 5.0),
    GeographicCluster("CLUSTER_HYD_KUKATPALLY", "Kukatpally Housing Board Node", "Hyderabad", "Telangana", "SOUTH_ZONE_METRO", 17.4933, 78.3986, 5.0),

    # Kolkata - East Zone
    GeographicCluster("CLUSTER_KOL_SALTLAKE", "Salt Lake Sector V Tech Center", "Kolkata", "West Bengal", "EAST_ZONE_METRO", 22.5769, 88.4339, 5.0),
    GeographicCluster("CLUSTER_KOL_PARKSTREET", "Park Street & BBD Bagh Central", "Kolkata", "West Bengal", "EAST_ZONE_METRO", 22.5535, 88.3519, 4.0),
    GeographicCluster("CLUSTER_KOL_NEWTOWN", "Rajarhat New Town Financial District", "Kolkata", "West Bengal", "EAST_ZONE_METRO", 22.5937, 88.4800, 6.0),
    GeographicCluster("CLUSTER_KOL_HOWRAH", "Howrah Railway & Wholesale Hub", "Howrah", "West Bengal", "EAST_ZONE_METRO", 22.5958, 88.2636, 5.0),

    # Pune - West Zone
    GeographicCluster("CLUSTER_PUN_HINJAWADI", "Hinjawadi Rajiv Gandhi Infotech Park", "Pune", "Maharashtra", "WEST_ZONE_METRO", 18.5913, 73.7389, 5.0),
    GeographicCluster("CLUSTER_PUN_SHIVAJINAGAR", "Shivajinagar & FC Road Center", "Pune", "Maharashtra", "WEST_ZONE_METRO", 18.5308, 73.8475, 4.0),
    GeographicCluster("CLUSTER_PUN_VIMANNAGAR", "Viman Nagar & Kharadi IT Hub", "Pune", "Maharashtra", "WEST_ZONE_METRO", 18.5679, 73.9143, 5.0),

    # Chennai - South Zone
    GeographicCluster("CLUSTER_CHE_TNAGAR", "T. Nagar Commercial & Retail District", "Chennai", "Tamil Nadu", "SOUTH_ZONE_METRO", 13.0418, 80.2341, 4.0),
    GeographicCluster("CLUSTER_CHE_OMR", "Old Mahabalipuram Road IT Expressway", "Chennai", "Tamil Nadu", "SOUTH_ZONE_METRO", 12.9345, 80.2312, 7.0),
    GeographicCluster("CLUSTER_CHE_ANNANAGAR", "Anna Nagar Central Node", "Chennai", "Tamil Nadu", "SOUTH_ZONE_METRO", 13.0850, 80.2101, 5.0),

    # Ahmedabad / Gandhinagar - West Zone
    GeographicCluster("CLUSTER_AHM_GIFTCITY", "GIFT City International Financial Centre", "Gandhinagar", "Gujarat", "WEST_ZONE_METRO", 23.1600, 72.6840, 5.0),
    GeographicCluster("CLUSTER_AHM_SGHIGHWAY", "SG Highway Corporate Corridor", "Ahmedabad", "Gujarat", "WEST_ZONE_METRO", 23.0338, 72.5070, 6.0),

    # Jaipur - North Zone
    GeographicCluster("CLUSTER_JAI_MIROAD", "MI Road & C-Scheme Financial Center", "Jaipur", "Rajasthan", "NORTH_ZONE_METRO", 26.9157, 75.8080, 5.0),

    # Lucknow - North Zone
    GeographicCluster("CLUSTER_LKO_HAZRATGANJ", "Hazratganj & Gomti Nagar Financial Node", "Lucknow", "Uttar Pradesh", "NORTH_ZONE_METRO", 26.8467, 80.9462, 6.0),

    # Chandigarh Tricity - North Zone
    GeographicCluster("CLUSTER_CHD_SEC17", "Sector 17 & Mohali IT Corridor", "Chandigarh", "Chandigarh UT", "NORTH_ZONE_METRO", 30.7398, 76.7827, 6.0),

    # Kochi - South Zone
    GeographicCluster("CLUSTER_KOC_INFOPARK", "Kakkanad Infopark & MG Road", "Kochi", "Kerala", "SOUTH_ZONE_METRO", 9.9816, 76.2999, 6.0),

    # Indore - Central Zone
    GeographicCluster("CLUSTER_IND_VIJAYNAGAR", "Vijay Nagar & AB Road Commercial District", "Indore", "Madhya Pradesh", "CENTRAL_ZONE_METRO", 22.7533, 75.8937, 5.0),
]


# Indian Payment Channels and typical constraints
PAYMENT_CHANNELS = ["UPI", "IMPS", "NEFT", "RTGS", "ATM", "wallet", "card"]

# Common Indian Cybercrime Modus Operandi (NCRP / 1930)
FRAUD_TYPES = [
    "upi_fraud",
    "phishing",
    "social_engineering",
    "investment_scam",
    "remote_access_scam",
    "account_takeover",
    "digital_arrest_scam",
    "loan_app_extortion",
]

# Account types and profile types
ACCOUNT_TYPES = ["individual", "business", "wallet", "intermediary"]
ACCOUNT_STATUSES = ["active", "dormant", "restricted", "closed"]
SYNTHETIC_PROFILE_TYPES = ["normal", "high_volume", "intermediary", "synthetic_mule_candidate"]

# Location types
LOCATION_TYPES = ["atm", "branch", "csp_kiosk", "pos_merchant"]

# Complaint Statuses
COMPLAINT_STATUSES = ["registered", "under_investigation", "frozen", "closed"]

# Synthetic Indian complaint narrative templates
COMPLAINT_TEMPLATES = {
    "upi_fraud": [
        "Victim received a fake QR code on WhatsApp for OLX item sale; scanning resulted in unauthorized UPI debit of INR {amount}.",
        "Fraudster impersonated electricity board officer asking for immediate UPI bill clearance of INR {amount} via phishing link.",
        "Fake customer care executive guided victim to enter UPI PIN on a deceptive merchant portal resulting in deduction of INR {amount}.",
        "Victim attempted to pay broadband bill using Google Pay/PhonePe and fell for fake helpline number, losing INR {amount}.",
    ],
    "phishing": [
        "Victim clicked on an SMS link claiming bank account KYC suspension, entered credentials and OTP, losing INR {amount}.",
        "Victim downloaded a malicious APK file ('SBI_Reward_Card.apk') received via SMS which intercepted OTPs for INR {amount} transfer.",
        "Phishing email mimicking income tax refund portal prompted victim to enter net banking credentials, draining INR {amount}.",
    ],
    "social_engineering": [
        "Victim was added to a Telegram 'Work From Home / YouTube Video Liking' group and scammed into depositing INR {amount}.",
        "Impersonation scam where fraudster claimed to be victim's close relative facing medical emergency at Mumbai airport, taking INR {amount}.",
        "Fraudster posed as an army officer purchasing furniture on Quikr, sending a reverse UPI payment request of INR {amount}.",
    ],
    "investment_scam": [
        "Victim lured into high-yield algorithmic crypto trading scheme promising 200% weekly return, transferring INR {amount} in tranches.",
        "Fake institutional stock trading platform app ('MaxWealth VIP / Institutional Club') defrauded victim of INR {amount} under pre-IPO allocation guarantee.",
        "WhatsApp group offering exclusive daily institutional equity tips convinced victim to transfer INR {amount} to dedicated current accounts.",
    ],
    "remote_access_scam": [
        "Fraudster claiming to be broadband tech support instructed victim to install AnyDesk/TeamViewer, capturing net banking transfer of INR {amount}.",
        "Victim received fake bank refund call and was asked to download QuickSupport app, resulting in unauthorized IMPS debit of INR {amount}.",
        "Fake credit card reward points redemption executive accessed phone via RustDesk and transferred INR {amount}.",
    ],
    "account_takeover": [
        "Victim experienced unauthorized SIM swap fraud followed by password reset and RTGS fund siphon of INR {amount}.",
        "Credential stuffing attack on victim's net banking portal followed by unauthorized beneficiary addition and transfer of INR {amount}.",
        "Stolen debit card credentials and OTP bypass resulted in unauthorized multi-tranche transfer of INR {amount}.",
    ],
    "digital_arrest_scam": [
        "Fraudsters impersonated CBI and Mumbai Cyber Crime officers via Skype video call claiming illegal parcels in victim's name, coercing transfer of INR {amount} for verification.",
        "Victim was placed under 'digital arrest' by fake Telecom Regulatory Authority officials threatening immediate arrest unless INR {amount} was wired to a secure RBI verification account.",
        "Fake Customs and Narcotics Control Bureau officers threatened victim with money laundering charges, extorting INR {amount} to clear their name.",
    ],
    "loan_app_extortion": [
        "Illegal instant loan app accessed victim's contact list and extorted INR {amount} through aggressive morphing harassment and multiple UPI demands.",
        "Victim took small micro-loan on unverified lending app and was forced under blackmail to pay INR {amount} across multiple mule accounts.",
    ],
}


@dataclass
class GenerationConfig:
    """Configuration settings for CASHNET Synthetic Data Generation Engine."""
    seed: int = 42
    profile: str = "standard"  # 'small', 'standard', 'large', 'dev', 'demo', 'custom'
    num_complaints: int = 5000
    num_accounts: int = 10000
    num_transactions: int = 65000
    num_locations: int = 300
    candidates_per_snapshot: int = 7
    suspicious_account_ratio: float = 0.14  # 12% - 16%
    future_cashout_rate: float = 0.42  # 35% - 48% target of eligible prediction-mode cases
    time_horizon_days: int = 90
    base_date: datetime = field(default_factory=lambda: datetime(2026, 6, 1, 0, 0, 0, tzinfo=timezone.utc))
    currency: str = "INR"
    data_dir: Path = field(default_factory=lambda: Path("data_v2"))
    db_url: Optional[str] = "sqlite:///./cashnet_dev.db"
    overwrite: bool = True

    @classmethod
    def from_profile(cls, profile_name: str, seed: int = 42, **kwargs) -> "GenerationConfig":
        """Builds configuration from predefined profile.

        Supported profiles:
        - small / dev: Fast iteration for local test suite and development (~300 cases, ~800 accounts, ~4k txns)
        - standard / demo: Primary ML model training & evaluation profile (~5k cases, ~10k accounts, ~65k txns, ~300 locs)
        - large: Stress-testing & scalability profile (~15k cases, ~25k accounts, ~180k txns, ~600 locs)
        - custom: User-specified parameters
        """
        profile_lower = profile_name.lower()
        if profile_lower in ["small", "dev"]:
            return cls(
                seed=seed,
                profile="small",
                num_complaints=kwargs.get("num_complaints", 300),
                num_accounts=kwargs.get("num_accounts", 800),
                num_transactions=kwargs.get("num_transactions", 4000),
                num_locations=kwargs.get("num_locations", 60),
                candidates_per_snapshot=kwargs.get("candidates_per_snapshot", 6),
                time_horizon_days=kwargs.get("time_horizon_days", 30),
                future_cashout_rate=kwargs.get("future_cashout_rate", 0.42),
                **{k: v for k, v in kwargs.items() if k not in [
                    "num_complaints", "num_accounts", "num_transactions", "num_locations",
                    "candidates_per_snapshot", "time_horizon_days", "future_cashout_rate"
                ]}
            )
        elif profile_lower in ["standard", "demo"]:
            return cls(
                seed=seed,
                profile="standard",
                num_complaints=kwargs.get("num_complaints", 5000),
                num_accounts=kwargs.get("num_accounts", 10000),
                num_transactions=kwargs.get("num_transactions", 65000),
                num_locations=kwargs.get("num_locations", 300),
                candidates_per_snapshot=kwargs.get("candidates_per_snapshot", 7),
                time_horizon_days=kwargs.get("time_horizon_days", 90),
                future_cashout_rate=kwargs.get("future_cashout_rate", 0.42),
                **{k: v for k, v in kwargs.items() if k not in [
                    "num_complaints", "num_accounts", "num_transactions", "num_locations",
                    "candidates_per_snapshot", "time_horizon_days", "future_cashout_rate"
                ]}
            )
        elif profile_lower == "large":
            return cls(
                seed=seed,
                profile="large",
                num_complaints=kwargs.get("num_complaints", 15000),
                num_accounts=kwargs.get("num_accounts", 25000),
                num_transactions=kwargs.get("num_transactions", 180000),
                num_locations=kwargs.get("num_locations", 600),
                candidates_per_snapshot=kwargs.get("candidates_per_snapshot", 8),
                time_horizon_days=kwargs.get("time_horizon_days", 120),
                future_cashout_rate=kwargs.get("future_cashout_rate", 0.42),
                **{k: v for k, v in kwargs.items() if k not in [
                    "num_complaints", "num_accounts", "num_transactions", "num_locations",
                    "candidates_per_snapshot", "time_horizon_days", "future_cashout_rate"
                ]}
            )
        else:
            return cls(seed=seed, profile="custom", **kwargs)
