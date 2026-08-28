"""
WeatherGPT - Member 3
Hazard Detection Schemas

Defines standardized structures for representing detected
weather hazards and their severity.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, ConfigDict

from schemas.risk import RiskLevel


class HazardType(str, Enum):
    """
    Standard weather hazard categories supported by WeatherGPT.
    """

    CYCLONE = "CYCLONE"
    FLOOD = "FLOOD"
    HEAVY_RAINFALL = "HEAVY_RAINFALL"
    HEATWAVE = "HEATWAVE"
    EXTREME_WIND = "EXTREME_WIND"
    EXTREME_WEATHER = "EXTREME_WEATHER"


class HazardResult(BaseModel):
    """
    Represents a detected weather hazard.

    This model is produced by hazard detection engines such as
    cyclone.py, flood.py, and heatwave.py.
    """

    model_config = ConfigDict(
        validate_assignment=True
    )

    hazard_type: HazardType = Field(
        ...,
        description="Type of weather hazard detected."
    )

    severity: RiskLevel = Field(
        ...,
        description="Severity level of the detected hazard."
    )

    score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Normalized hazard severity score from 0 to 100."
    )

    confidence: float = Field(
        ...,
        ge=0,
        le=1,
        description="Confidence in the hazard detection, from 0 to 1."
    )

    reason: str = Field(
        ...,
        min_length=1,
        description="Reason explaining why the hazard was detected."
    )

    location_name: str | None = Field(
        default=None,
        description="Location associated with the detected hazard."
    )

    timestamp: datetime = Field(
        ...,
        description="Time at which the hazard was detected."
    )