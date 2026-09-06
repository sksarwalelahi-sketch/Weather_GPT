"""
WeatherGPT - Member 3
Intelligence Service

Application-facing orchestration layer for Member 3.

Responsibilities:
    - Fetch weather data from Member 1
    - Convert Member 1 responses using the integration adapters
    - Run the existing Member 3 intelligence engines
    - Expose simple methods for downstream consumers

This service does NOT:
    - fetch weather data directly from Open-Meteo
    - modify Member 1 API responses
    - perform field mapping itself
    - implement risk/hazard/advisory logic

Those responsibilities belong to:
    Member 1          -> Weather data
    member1_client   -> HTTP communication
    member1_adapter  -> Data transformation
    intelligence.*   -> Intelligence calculations
"""

from __future__ import annotations

from datetime import date
from typing import Any

from integration.member1_adapter import (
    current_to_weather_input,
    forecast_to_weather_inputs,
    historical_to_climate_values,
)
from integration.member1_client import Member1Client
from intelligence.decision import analyze_weather
from intelligence.forecast import analyze_forecast
from schemas.forecast import ForecastAnalysis
from schemas.intelligence import WeatherIntelligenceResult


class IntelligenceService:
    """
    Public application-facing service for Member 3.

    Downstream components such as Member 2, Member 4, and Member 5
    should use this service instead of directly depending on the
    Member 1 client, adapters, and intelligence engines.
    """

    def __init__(
        self,
        client: Member1Client | None = None,
    ) -> None:
        """
        Initialize the intelligence service.

        Parameters
        ----------
        client:
            Optional Member 1 API client.

            If omitted, a default Member1Client is created. The
            client itself resolves MEMBER1_API_URL from the
            environment when configured.
        """

        self.client = client or Member1Client()

    # ------------------------------------------------------------------
    # Current Weather Intelligence
    # ------------------------------------------------------------------

    def analyze_current(
        self,
        latitude: float,
        longitude: float,
        location_name: str | None = None,
    ) -> WeatherIntelligenceResult:
        """
        Fetch current weather from Member 1 and run the complete
        Member 3 intelligence pipeline.

        Returns
        -------
        WeatherIntelligenceResult
            Risk, hazards, alerts, advisories, and other current
            weather intelligence.
        """

        payload = self.client.get_current(
            latitude=latitude,
            longitude=longitude,
        )

        weather = current_to_weather_input(
            payload=payload,
            location_name=location_name,
        )

        return analyze_weather(weather)

    # ------------------------------------------------------------------
    # Forecast Intelligence
    # ------------------------------------------------------------------

    def analyze_forecast(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
        location_name: str | None = None,
    ) -> ForecastAnalysis:
        """
        Fetch the Member 1 daily forecast and analyze the complete
        forecast period.

        Parameters
        ----------
        latitude:
            Location latitude.

        longitude:
            Location longitude.

        forecast_days:
            Number of forecast days requested from Member 1.
            Must be between 1 and 16.

        location_name:
            Optional human-readable location name.

        Returns
        -------
        ForecastAnalysis
            Chronologically ordered forecast intelligence.
        """

        payload = self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

        weather_points = forecast_to_weather_inputs(
            payload=payload,
            location_name=location_name,
        )

        return analyze_forecast(
            weather_points=weather_points,
            location_name=location_name,
        )

    # ------------------------------------------------------------------
    # Current Weather + Historical Climate Intelligence
    # ------------------------------------------------------------------

    def analyze_current_with_history(
        self,
        latitude: float,
        longitude: float,
        start_date: date | str,
        end_date: date | str,
        baselines: dict[str, float],
        location_name: str | None = None,
    ) -> WeatherIntelligenceResult:
        """
        Fetch current weather and historical weather data, then run
        current weather intelligence together with climate analysis.

        Parameters
        ----------
        latitude:
            Location latitude.

        longitude:
            Location longitude.

        start_date:
            Historical period start date.

        end_date:
            Historical period end date.

        baselines:
            Caller-supplied climate baselines.

            Example:
                {
                    "temperature": 30.0,
                    "rainfall": 5.0,
                    "wind_speed": 15.0,
                }

            The service does not invent or calculate baselines.

        location_name:
            Optional human-readable location name.

        Returns
        -------
        WeatherIntelligenceResult
            Current weather intelligence including climate analysis.
        """

        current_payload = self.client.get_current(
            latitude=latitude,
            longitude=longitude,
        )

        historical_payload = self.client.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )

        weather = current_to_weather_input(
            payload=current_payload,
            location_name=location_name,
        )

        historical_values = historical_to_climate_values(
            payload=historical_payload,
            baselines=baselines,
            location_name=location_name,
        )

        return analyze_weather(
            weather=weather,
            historical_values=historical_values,
        )

    # ------------------------------------------------------------------
    # Raw Member 1 Access
    # ------------------------------------------------------------------

    def get_current_data(
        self,
        latitude: float,
        longitude: float,
    ) -> dict[str, Any]:
        """
        Return the raw current-weather response from Member 1.

        This method is intentionally provided only as a thin access
        method for integration/debugging use cases.

        Intelligence calculations should use analyze_current().
        """

        return self.client.get_current(
            latitude=latitude,
            longitude=longitude,
        )

    def get_forecast_data(
        self,
        latitude: float,
        longitude: float,
        forecast_days: int = 7,
    ) -> dict[str, Any]:
        """
        Return the raw forecast response from Member 1.
        """

        return self.client.get_forecast(
            latitude=latitude,
            longitude=longitude,
            forecast_days=forecast_days,
        )

    def get_historical_data(
        self,
        latitude: float,
        longitude: float,
        start_date: date | str,
        end_date: date | str,
    ) -> dict[str, Any]:
        """
        Return the raw historical response from Member 1.
        """

        return self.client.get_historical(
            latitude=latitude,
            longitude=longitude,
            start_date=start_date,
            end_date=end_date,
        )