"""
WeatherGPT - Member 3
Weather Input Schema

Defines the standardized weather data structure consumed by
the Weather Intelligence and Decision-Support Engine.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class WeatherInput(BaseModel):
    """
    Standardized weather input for the Member 3 intelligence engine.

    This model is designed to act as an internal contract between
    the data/NWP layer and the intelligence layer.
    """

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True
    )

    # ------------------------------------------------------------------
    # Location
    # ------------------------------------------------------------------

    location_name: Optional[str] = Field(
        default=None,
        description="Human-readable name of the observation/forecast location."
    )

    latitude: float = Field(
        ...,
        ge=-90,
        le=90,
        description="Latitude of the location in decimal degrees."
    )

    longitude: float = Field(
        ...,
        ge=-180,
        le=180,
        description="Longitude of the location in decimal degrees."
    )

    # ------------------------------------------------------------------
    # Time
    # ------------------------------------------------------------------

    timestamp: datetime = Field(
        ...,
        description="Timestamp of the weather observation or forecast."
    )

    # ------------------------------------------------------------------
    # Temperature
    # ------------------------------------------------------------------

    temperature: Optional[float] = Field(
        default=None,
        description="Air temperature in degrees Celsius."
    )

    feels_like: Optional[float] = Field(
        default=None,
        description="Feels-like temperature in degrees Celsius."
    )

    # ------------------------------------------------------------------
    # Atmospheric conditions
    # ------------------------------------------------------------------

    humidity: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Relative humidity in percentage."
    )

    pressure: Optional[float] = Field(
        default=None,
        ge=0,
        description="Atmospheric pressure in hPa."
    )

    # ------------------------------------------------------------------
    # Rainfall / precipitation
    # ------------------------------------------------------------------

    rainfall: Optional[float] = Field(
        default=None,
        ge=0,
        description="Observed or forecast rainfall in millimetres."
    )

    precipitation_probability: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Probability of precipitation in percentage."
    )

    # ------------------------------------------------------------------
    # Wind
    # ------------------------------------------------------------------

    wind_speed: Optional[float] = Field(
        default=None,
        ge=0,
        description="Wind speed in kilometres per hour."
    )

    wind_direction: Optional[float] = Field(
        default=None,
        ge=0,
        le=360,
        description="Wind direction in degrees."
    )

    wind_gust: Optional[float] = Field(
        default=None,
        ge=0,
        description="Maximum wind gust in kilometres per hour."
    )

    # ------------------------------------------------------------------
    # Visibility
    # ------------------------------------------------------------------

    visibility: Optional[float] = Field(
        default=None,
        ge=0,
        description="Horizontal visibility in kilometres."
    )

    # ------------------------------------------------------------------
    # Data provenance
    # ------------------------------------------------------------------

    source: Optional[str] = Field(
        default=None,
        description="Source of the weather data, such as IMD, GFS, WRF, or API."
    )

    # ------------------------------------------------------------------
    # Forecast metadata
    # ------------------------------------------------------------------

    forecast_horizon_hours: Optional[int] = Field(
        default=None,
        ge=0,
        description="Forecast horizon represented by this weather record."
    )