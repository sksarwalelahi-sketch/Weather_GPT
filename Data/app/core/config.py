import os

from dotenv import load_dotenv


from pathlib import Path

# Load variables from the project's .env file (supports running from any CWD).
_env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(_env_path if _env_path.exists() else None)
load_dotenv()


class Settings:
    APP_NAME = os.getenv(
        "APP_NAME",
        "WeatherGPT Weather Data Platform",
    )

    APP_VERSION = os.getenv(
        "APP_VERSION",
        "0.1.0",
    )

    API_PREFIX = os.getenv(
        "API_PREFIX",
        "/api",
    )

    # Open-Meteo exposes these NWP models without requiring local GRIB parsing.
    OPEN_METEO_NWP_MODELS = os.getenv(
        "OPEN_METEO_NWP_MODELS",
        "gfs_seamless,ecmwf_ifs025",
    )

    MONGODB_URI = os.getenv(
        "MONGODB_URI",
        "mongodb://localhost:27017",
    )

    MONGODB_DATABASE = os.getenv(
        "MONGODB_DATABASE",
        "weathergpt",
    )

    MONGODB_SERVER_SELECTION_TIMEOUT_MS = int(
        os.getenv(
            "MONGODB_SERVER_SELECTION_TIMEOUT_MS",
            "15000",
        )
    )

    MONGODB_STARTUP_RETRIES = int(
        os.getenv(
            "MONGODB_STARTUP_RETRIES",
            "3",
        )
    )

    MONGODB_STARTUP_RETRY_DELAY_SECONDS = float(
        os.getenv(
            "MONGODB_STARTUP_RETRY_DELAY_SECONDS",
            "5",
        )
    )

    REDIS_HOST = os.getenv(
        "REDIS_HOST",
        "127.0.0.1",
    )

    REDIS_PORT = int(
        os.getenv(
            "REDIS_PORT",
            "6379",
        )
    )

    REDIS_DB = int(
        os.getenv(
            "REDIS_DB",
            "0",
        )
    )

    IMD_API_URL = os.getenv(
        "IMD_API_URL",
        "https://city.imd.gov.in/api/cityweather_loc.php",
    )

    IMD_OFFICIAL_PORTAL_URL = os.getenv(
        "IMD_OFFICIAL_PORTAL_URL",
        "https://mausam.imd.gov.in/",
    )

    # ------------------------------------------------------------------
    # IMD Official API Portal (api.imd.gov.in) — new integration
    # ------------------------------------------------------------------

    # Portal credentials (used for JWT token refresh)
    IMD_API_BASE = os.getenv("IMD_API_BASE", "https://api.imd.gov.in/api/v1").rstrip("/")
    IMD_EMAIL = os.getenv("IMD_EMAIL", "")
    IMD_PASSWORD = os.getenv("IMD_PASSWORD", "")

    # API Keys (IP-bound; 2 Dev + 2 Prod)
    # Dev Key 1: current_wx / stationnowcast / districtnowcast / aws_data
    IMD_DEV_KEY_1 = os.getenv("IMD_DEV_KEY_1", "")
    # Dev Key 2: cityforecastloc / cityforecastwarning / districtwarning / districtrainfall
    IMD_DEV_KEY_2 = os.getenv("IMD_DEV_KEY_2", "")
    # Prod Key 1 & 2 (same functional split, different IP)
    IMD_PROD_KEY_1 = os.getenv("IMD_PROD_KEY_1", "")
    IMD_PROD_KEY_2 = os.getenv("IMD_PROD_KEY_2", "")

    # Active keys (swap to PROD_KEY_* in production environment)
    IMD_ACTIVE_KEY_1 = os.getenv("IMD_ACTIVE_KEY_1", IMD_DEV_KEY_1)
    IMD_ACTIVE_KEY_2 = os.getenv("IMD_ACTIVE_KEY_2", IMD_DEV_KEY_2)

    # API endpoint path suffixes (relative to https://api.imd.gov.in/api/)
    IMD_ENDPOINT_CURRENT_WX = os.getenv("IMD_ENDPOINT_CURRENT_WX", "current_wx")
    IMD_ENDPOINT_STATION_NOWCAST = os.getenv("IMD_ENDPOINT_STATION_NOWCAST", "stationnowcast")
    IMD_ENDPOINT_DISTRICT_NOWCAST = os.getenv("IMD_ENDPOINT_DISTRICT_NOWCAST", "districtnowcast")
    IMD_ENDPOINT_AWS = os.getenv("IMD_ENDPOINT_AWS", "aws_data")
    IMD_ENDPOINT_CITY_FORECAST = os.getenv("IMD_ENDPOINT_CITY_FORECAST", "cityforecastloc")
    IMD_ENDPOINT_CITY_FORECAST_WARNING = os.getenv("IMD_ENDPOINT_CITY_FORECAST_WARNING", "cityforecastwarning")
    IMD_ENDPOINT_DISTRICT_WARNING = os.getenv("IMD_ENDPOINT_DISTRICT_WARNING", "districtwarning")
    IMD_ENDPOINT_DISTRICT_RAINFALL = os.getenv("IMD_ENDPOINT_DISTRICT_RAINFALL", "districtrainfall")
    IMD_ENDPOINT_TOURIST_FORECAST = os.getenv("IMD_ENDPOINT_TOURIST_FORECAST", "touristforecast")
    IMD_ENDPOINT_SUNMOON = os.getenv("IMD_ENDPOINT_SUNMOON", "sunmoon")

    # Legacy warning poll (kept for backward compatibility)
    IMD_WARNINGS_URL = os.getenv("IMD_WARNINGS_URL", "")
    IMD_WARNINGS_API_KEY = os.getenv("IMD_WARNINGS_API_KEY", "")
    IMD_WARNINGS_ENABLED = os.getenv("IMD_WARNINGS_ENABLED", "false").lower() == "true"
    IMD_WARNINGS_POLL_MINUTES = int(os.getenv("IMD_WARNINGS_POLL_MINUTES", "10"))

    NDMA_SACHET_API_URL = os.getenv("NDMA_SACHET_API_URL", "").rstrip("/")
    NDMA_SACHET_ENABLED = os.getenv("NDMA_SACHET_ENABLED", "false").lower() == "true"
    NOAA_ALERTS_API_URL = os.getenv(
        "NOAA_ALERTS_API_URL",
        "https://api.weather.gov/alerts/active",
    ).rstrip("/")
    OPEN_METEO_FLOOD_API_URL = os.getenv(
        "OPEN_METEO_FLOOD_API_URL",
        "https://flood-api.open-meteo.com/v1/flood",
    ).rstrip("/")
    ALERT_PROVIDER_TIMEOUT_SECONDS = float(
        os.getenv("ALERT_PROVIDER_TIMEOUT_SECONDS", "10")
    )

    INTELLIGENCE_API_URL = os.getenv(
        "INTELLIGENCE_API_URL",
        "http://127.0.0.1:8001",
    ).rstrip("/")

    MOSDAC_API_URL = os.getenv(
        "MOSDAC_API_URL",
        "",
    )

    MOSDAC_CATALOG_URL = os.getenv(
        "MOSDAC_CATALOG_URL",
        "https://mosdac.gov.in/apios/datasets.json",
    )

    MOSDAC_DATASET_ID = os.getenv(
        "MOSDAC_DATASET_ID",
        "3RIMG_L2B_SST",
    )

    # Flood providers are intentionally opt-in because NOAA NWM, ECMWF EFAS,
    # and DWD expose different products and access requirements.
    NOAA_FLOOD_API_URL = os.getenv("NOAA_FLOOD_API_URL", "").rstrip("/")
    ECMWF_FLOOD_API_URL = os.getenv("ECMWF_FLOOD_API_URL", "").rstrip("/")
    DWD_FLOOD_API_URL = os.getenv("DWD_FLOOD_API_URL", "").rstrip("/")
    FLOOD_PROVIDER_TIMEOUT_SECONDS = float(
        os.getenv("FLOOD_PROVIDER_TIMEOUT_SECONDS", "10")
    )

    WIS2_BROKER_HOST = os.getenv(
        "WIS2_BROKER_HOST",
        "globalbroker.meteo.fr",
    )

    WIS2_BROKER_PORT = int(
        os.getenv(
            "WIS2_BROKER_PORT",
            "8883",
        )
    )

    WIS2_BROKER_USERNAME = os.getenv(
        "WIS2_BROKER_USERNAME",
        "everyone",
    )

    WIS2_BROKER_PASSWORD = os.getenv(
        "WIS2_BROKER_PASSWORD",
        "everyone",
    )

    WIS2_TOPIC = os.getenv(
        "WIS2_TOPIC",
        "origin/a/wis2/#",
    )
    WIS2_WARNINGS_ENABLED = os.getenv("WIS2_WARNINGS_ENABLED", "false").lower() == "true"

    INGESTION_WORKER_COUNT = int(
        os.getenv("INGESTION_WORKER_COUNT", "4")
    )

    INGESTION_MAX_RETRIES = int(
        os.getenv("INGESTION_MAX_RETRIES", "3")
    )

    INGESTION_RETRY_BASE_SECONDS = float(
        os.getenv("INGESTION_RETRY_BASE_SECONDS", "1")
    )

    # Semicolon-separated latitude,longitude pairs.
    SCHEDULER_LOCATIONS = os.getenv(
        "SCHEDULER_LOCATIONS",
        "20.2961,85.8245",
    )

    API_KEYS = frozenset(
        key.strip()
        for key in os.getenv("API_KEYS", "").split(",")
        if key.strip()
    )

    RATE_LIMIT_PER_MINUTE = int(
        os.getenv("RATE_LIMIT_PER_MINUTE", "120")
    )

    CORS_ORIGINS = tuple(
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://localhost:5173",
        ).split(",")
        if origin.strip()
    )

settings = Settings()


def get_scheduler_locations() -> tuple[tuple[float, float], ...]:
    """Parse and validate configured scheduler coordinates."""
    locations: list[tuple[float, float]] = []

    for index, value in enumerate(
        settings.SCHEDULER_LOCATIONS.split(";"),
        start=1,
    ):
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 2:
            raise ValueError(
                "SCHEDULER_LOCATIONS entry "
                f"{index} must be 'latitude,longitude'"
            )

        try:
            latitude, longitude = (
                float(parts[0]),
                float(parts[1]),
            )
        except ValueError as exc:
            raise ValueError(
                "SCHEDULER_LOCATIONS entry "
                f"{index} contains invalid coordinates"
            ) from exc

        if not -90 <= latitude <= 90:
            raise ValueError(
                f"SCHEDULER_LOCATIONS entry {index} "
                "has latitude outside -90..90"
            )
        if not -180 <= longitude <= 180:
            raise ValueError(
                f"SCHEDULER_LOCATIONS entry {index} "
                "has longitude outside -180..180"
            )

        locations.append((latitude, longitude))

    if not locations:
        raise ValueError(
            "SCHEDULER_LOCATIONS must contain at least one location"
        )

    return tuple(locations)
