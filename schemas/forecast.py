"""
WeatherGPT - Member 3
Forecast Analysis Schemas

Defines standardized structures for forecast intelligence,
future weather risk analysis, and forecast summaries.
"""

from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict

from schemas.hazard import HazardResult
from schemas.risk import RiskAssessment
from schemas.weather import WeatherInput


class ForecastPoint(BaseModel):
    """
    Represents one forecast point with its associated
    weather conditions and intelligence outputs.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    weather: WeatherInput = Field(
        ...,
        description="Weather forecast data for this time point.",
    )

    risk_assessment: RiskAssessment | None = Field(
        default=None,
        description="Risk assessment for the forecast conditions.",
    )

    hazards: list[HazardResult] = Field(
        default_factory=list,
        description="Hazards detected for this forecast point.",
    )


class ForecastAnalysis(BaseModel):
    """
    Complete forecast intelligence result.

    Contains the forecast time range, forecast points,
    detected hazards, maximum risk, and a human-readable
    summary.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    location_name: str = Field(
        ...,
        min_length=1,
        description="Location associated with the forecast.",
    )

    generated_at: datetime = Field(
        ...,
        description="Timestamp when the forecast analysis was generated.",
    )

    forecast_start: datetime = Field(
        ...,
        description="Start time of the forecast period.",
    )

    forecast_end: datetime = Field(
        ...,
        description="End time of the forecast period.",
    )

    forecast_points: list[ForecastPoint] = Field(
        default_factory=list,
        description="Chronologically ordered forecast points.",
    )

    maximum_risk_level: str = Field(
        ...,
        min_length=1,
        description="Highest risk level found during the forecast period.",
    )

    maximum_risk_score: float = Field(
        default=0.0,
        ge=0,
        le=100,
        description="Highest risk score found during the forecast period.",
    )

    hazards: list[HazardResult] = Field(
        default_factory=list,
        description="Unique hazards detected across the forecast period.",
    )

    summary: str = Field(
        ...,
        min_length=1,
        description="Human-readable summary of forecast conditions.",
    )

    confidence: float = Field(
        default=0.0,
        ge=0,
        le=1,
        description="Overall confidence based on forecast data coverage.",
    )

    source: str | None = Field(
        default=None,
        description="Forecast data source.",
    )

    data_points: int = Field(
        default=0,
        ge=0,
        description="Number of forecast observations analysed.",
    )